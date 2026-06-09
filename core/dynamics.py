import numpy as np
from dataclasses import dataclass
from typing import Tuple

@dataclass
class SystemStateVector:
    position_s: float       # Local position coordinate along tracking track (m)
    velocity_v: float       # Absolute vehicle velocity profile state (m/s)
    battery_soc: float      # Extracted charge balance status fraction [0.0, 1.0]
    cumulative_energy_j: float # Cumulative electrical energy used up to current node (J)
    throttle_u: float = 0.0 # Throttle input (0 for coast, 1 for burst)
    power_elec_w: float = 0.0 # Instantaneous electrical power (W)
    current_batt_a: float = 0.0 # Instantaneous battery current draw (A)
    motor_efficiency: float = 0.0 # Instantaneous motor efficiency

def calculate_aerodynamic_drag(v: np.ndarray, rho_a: float, cd_af: float, v_w: np.ndarray, phi_veh: np.ndarray, phi_wind: float) -> np.ndarray:
    """
    Calculate aerodynamic drag force.
    F_w(s) = 0.5 * rho_a * C_D_A_f * (v(s) + v_w * cos(phi_veh(s) - phi_wind))^2
    """
    return 0.5 * rho_a * cd_af * (v + v_w * np.cos(phi_veh - phi_wind))**2

def calculate_rolling_resistance(v: np.ndarray, M_v: float, g: float, theta: np.ndarray, crr: float = 0.01) -> np.ndarray:
    """
    Calculate rolling resistance force.
    F_r(s) = M_v * g * f_r(v) * cos(theta(s))
    f_r(v) = crr * (1 + 3.6 * v(s) / 100)  # localized linear relationship
    """
    f_r = crr * (1.0 + (3.6 * v) / 100.0)
    return M_v * g * f_r * np.cos(theta)

def calculate_gradient_resistance(M_v: float, g: float, theta: np.ndarray) -> np.ndarray:
    """
    Calculate gradient resistance force.
    F_g(s) = M_v * g * sin(theta(s))
    """
    return M_v * g * np.sin(theta)

def calculate_axle_normal_loads(
    F_trac: np.ndarray, F_r: np.ndarray, 
    M_v: float, g: float, theta: np.ndarray,
    L_a: float, L_b: float, h_g: float, r_d: float
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate front and rear axle normal loads.
    L = L_a + L_b
    W_f(s) = (L_b/L)*M_v*g*cos(theta) - (h_g/L)*(F_trac - F_r*(1 - r_d/h_g))
    W_r(s) = (L_a/L)*M_v*g*cos(theta) + (h_g/L)*(F_trac - F_r*(1 - r_d/h_g))
    """
    L = L_a + L_b
    weight_component = M_v * g * np.cos(theta)
    load_transfer = (h_g / L) * (F_trac - F_r * (1.0 - r_d / h_g))
    
    W_f = (L_b / L) * weight_component - load_transfer
    W_r = (L_a / L) * weight_component + load_transfer
    
    return W_f, W_r
