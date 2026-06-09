import numpy as np
from typing import List, Tuple, Dict, Any
from core.track import NormalizedTrackNode
from core.dynamics import (
    SystemStateVector, calculate_aerodynamic_drag,
    calculate_rolling_resistance, calculate_gradient_resistance
)
from core.powertrain import (
    calculate_motor_rpm, calculate_motor_torque,
    calculate_electrical_power, calculate_battery_state,
    clamp_motor_rpm, get_motor_efficiency
)

def compute_v_bounds(track_nodes: List[NormalizedTrackNode], mu_lat: float, g: float = 9.81) -> np.ndarray:
    v_bounds = []
    for node in track_nodes:
        if node.curvature <= 1e-6:
            v_bounds.append(float('inf'))
        else:
            v_bounds.append(np.sqrt((mu_lat * g) / node.curvature))
    return np.array(v_bounds)

def apply_human_repeatability_filter(
    control_vector: np.ndarray, 
    s_array: np.ndarray, 
    min_burst_dist: float = 15.0, 
    min_coast_dist: float = 40.0
) -> np.ndarray:
    filtered = np.copy(control_vector)
    if len(filtered) == 0: return filtered
    
    current_state = filtered[0]
    state_start_idx = 0
    for i in range(1, len(filtered)):
        if filtered[i] != current_state:
            dist = s_array[i] - s_array[state_start_idx]
            if current_state == 1 and dist < min_burst_dist:
                filtered[i] = 1 
            elif current_state == 0 and dist < min_coast_dist:
                filtered[i] = 0 
            else:
                current_state = filtered[i]
                state_start_idx = i
    return filtered

def run_trajectory_optimization(
    track_nodes: List[NormalizedTrackNode], 
    vehicle_params: Dict[str, Any] = None,
    w_T: float = 10.0,    
    w_E: float = 1000.0,
    **kwargs
) -> Tuple[List[SystemStateVector], Dict[str, Any]]:
    if vehicle_params is None:
        vehicle_params = {
            'M_v': 110.0,
            'Cd': 0.332,
            'A': 0.388,
            'Crr': 0.005,
            'eta_motor_peak': 80.0,
            'eta_trans': 98.0,
            'r_w': 0.254,
            'G': 6.0,
            'Voc': 48.0,
            'I_max': 20.0,
            'V_min': 37.7,
            'V_max': 54.6,
            'target_time_s': 2100.0
        }
        
    if 'target_time_s' in kwargs:
        vehicle_params['target_time_s'] = kwargs['target_time_s']
        
    n_nodes = len(track_nodes)
    if n_nodes < 2:
        raise ValueError("Track must have at least 2 nodes")
        
    s_array = np.array([node.distance_m for node in track_nodes])
    theta_array = np.array([node.gradient_pct / 100.0 for node in track_nodes])
    
    # Vehicle Spec assumptions 
    M_v = vehicle_params.get('M_v', 110.0)
    g = 9.81
    rho_a = 1.225
    cd_af = vehicle_params.get('Cd', 0.332) * vehicle_params.get('A', 0.388)
    v_w = 0.0
    phi_veh = 0.0
    phi_wind = 0.0
    r_w = vehicle_params.get('r_w', 0.254)
    G = vehicle_params.get('G', 6.0)
    eta_trans = vehicle_params.get('eta_trans', 98.0) / 100.0
    eta_motor_peak = vehicle_params.get('eta_motor_peak', 80.0) / 100.0
    max_rpm = 4000.0
    mu_lat = 1.0
    Voc = vehicle_params.get('Voc', 48.0)
    R_int = 0.05
    max_burst_force = 120.0
    I_max = vehicle_params.get('I_max', 20.0)
    V_min = vehicle_params.get('V_min', 37.7)
    V_max = vehicle_params.get('V_max', 54.6)
    target_time_s = vehicle_params.get('target_time_s', 2100.0)
    crr = vehicle_params.get('Crr', 0.005)
    
    v_bounds = compute_v_bounds(track_nodes, mu_lat, g)
    max_v_rpm = (max_rpm * 2 * np.pi / 60.0) * r_w / G
    v_bounds = np.clip(v_bounds, 0.0, max_v_rpm)
    
    best_J = float('inf')
    best_states = []
    best_stats = {}
    best_control = None
    
    # 2D Grid sweep: Target speeds and Hysteresis width (delta_v) to strictly enforce burst/coast
    for v_target in np.linspace(6.0, 14.0, 10):
        for delta_v in np.linspace(0.5, 4.0, 8):
            v_min = v_target - delta_v
            v_max = v_target + delta_v
            
            states = []
            v = 0.1 
            time_elapsed = 0.0
            energy_j = 0.0
            soc = 1.0
            
            control_u = np.zeros(n_nodes)
            current_state = 1 # Start with burst
            last_transition_s = s_array[0]
            
            for i in range(n_nodes - 1):
                ds = s_array[i+1] - s_array[i]
                if ds <= 0: ds = 1.0
                    
                v_b = v_bounds[i]
                v = min(v, v_b)
                
                F_w = calculate_aerodynamic_drag(v, rho_a, cd_af, v_w, phi_veh, phi_wind)
                F_r = calculate_rolling_resistance(v, M_v, g, theta_array[i], crr)
                F_g = calculate_gradient_resistance(M_v, g, theta_array[i])
                F_res = F_w + F_r + F_g
                
                # Topography-aware checks:
                # 1. Detect descent (gradient_pct < -0.2%)
                is_descent = theta_array[i] < -0.002
                
                # 2. Detect climb ahead (scan the next 30 nodes for gradient_pct > 0.5%)
                climb_ahead = False
                lookahead_limit = min(i + 30, n_nodes - 1)
                for k in range(i + 1, lookahead_limit):
                    if theta_array[k] > 0.005:
                        climb_ahead = True
                        break
                
                # Strict Hysteresis Burst/Coast Control Policy
                desired_state = current_state
                if v <= v_min:
                    desired_state = 1
                elif v >= v_max or v >= v_b * 0.95:
                    desired_state = 0
                
                # Override based on topography context
                if is_descent:
                    desired_state = 0
                elif climb_ahead and v < v_max:
                    desired_state = 1
                
                # Enforce minimum segment lengths (spatial scheduler)
                dist_since_transition = s_array[i] - last_transition_s
                if desired_state != current_state:
                    if current_state == 1:
                        # Transition to Coast allowed only if active for >= 15m
                        if dist_since_transition >= 15.0:
                            current_state = 0
                            last_transition_s = s_array[i]
                    else:
                        # Transition to Burst allowed only if coasted for >= 40m
                        # and we are NOT in a descent zone
                        if dist_since_transition >= 40.0 and not is_descent:
                            current_state = 1
                            last_transition_s = s_array[i]
                            
                control_u[i] = current_state
                F_trac = max_burst_force if current_state == 1 else 0.0
                    
                P_elec, I_batt, Vt, eta_m = 0.0, 0.0, Voc, 0.0
                
                if F_trac > 0:
                    rpm = calculate_motor_rpm(v, r_w, G)
                    rpm = clamp_motor_rpm(rpm, max_rpm)
                    torque = calculate_motor_torque(F_trac, r_w, G, eta_trans)
                    eta_m = get_motor_efficiency(torque, rpm, eta_motor_peak)
                    P_elec = calculate_electrical_power(torque, rpm, eta_motor_peak, is_propulsion=True)
                    I_batt, Vt = calculate_battery_state(P_elec, Voc, R_int)
                    
                    # Enforce BMS current limit and voltage limits
                    I_max_eff = min(I_max, (Voc - V_min) / R_int)
                    if I_batt > I_max_eff:
                        P_elec = P_elec * (I_max_eff / max(I_batt, 1e-6))
                        I_batt, Vt = calculate_battery_state(P_elec, Voc, R_int)
                        
                    energy_step = P_elec * (ds / max(v, 0.1))
                    energy_j += energy_step
                    soc -= energy_step / 3.6e6 
                
                work = (F_trac - F_res) * ds
                v_new_sq = v**2 + (2 * work / M_v)
                v_new = np.sqrt(max(1.0, v_new_sq))
                    
                v = min(v_new, v_bounds[i+1])
                time_elapsed += ds / max(v, 0.1)
                
                states.append(SystemStateVector(
                    position_s=s_array[i],
                    velocity_v=v,
                    battery_soc=soc,
                    cumulative_energy_j=energy_j,
                    throttle_u=float(current_state),
                    power_elec_w=P_elec,
                    current_batt_a=I_batt,
                    motor_efficiency=eta_m
                ))
                
            states.append(SystemStateVector(
                position_s=s_array[-1],
                velocity_v=v,
                battery_soc=soc,
                cumulative_energy_j=energy_j,
                throttle_u=float(current_state),
                power_elec_w=0.0,
                current_batt_a=0.0,
                motor_efficiency=0.0
            ))
            
            time_penalty = max(0, time_elapsed - target_time_s)
            
            # Topography alignment penalty
            hill_penalty = 0.0
            for i in range(n_nodes):
                is_descent = theta_array[i] < -0.002
                climb_ahead = False
                lookahead_limit = min(i + 30, n_nodes - 1)
                for k in range(i + 1, lookahead_limit):
                    if theta_array[k] > 0.005:
                        climb_ahead = True
                        break
                
                # Penalize bursting during descents
                if control_u[i] == 1 and is_descent:
                    hill_penalty += 200.0 * (s_array[1] - s_array[0]) # weight by distance step
                # Penalize coasting when a climb is ahead
                if control_u[i] == 0 and climb_ahead:
                    hill_penalty += 10.0 * (s_array[1] - s_array[0])
            
            J = w_E * energy_j + w_T * (time_penalty**2) + hill_penalty
            
            if J < best_J and time_elapsed <= target_time_s:
                best_J = J
                filt_u = apply_human_repeatability_filter(control_u, s_array)
                for i in range(len(filt_u)):
                    states[i].throttle_u = float(filt_u[i])
                    
                transitions = np.sum(np.abs(np.diff(filt_u)))
                
                best_states = states
                best_stats = {
                    'time_s': time_elapsed,
                    'energy_j': energy_j,
                    'transitions': int(transitions),
                    'efficiency_km_kwh': (s_array[-1] / 1000.0) / (energy_j / 3.6e6) if energy_j > 0 else 0,
                    'target_speed': v_target,
                    'delta_v': delta_v,
                    'cost_J': J
                }
                
    if not best_states:
        best_stats = {
            'time_s': time_elapsed,
            'energy_j': energy_j,
            'transitions': int(np.sum(np.abs(np.diff(control_u)))),
            'efficiency_km_kwh': (s_array[-1] / 1000.0) / (energy_j / 3.6e6) if energy_j > 0 else 0,
            'warning': 'Target time limit exceeded by all strategies. Constraints might be too strict.'
        }
        best_states = states
        
    return best_states, best_stats
