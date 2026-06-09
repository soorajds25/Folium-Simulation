import numpy as np
from typing import Tuple

def calculate_motor_rpm(v: float, r_w: float, G: float) -> float:
    """
    Convert wheel linear velocity to motor shaft RPM.
    Omega_motor = (v / r_w) * G * (60 / (2 * pi))
    """
    if v < 0: return 0.0
    return (v / r_w) * G * (60.0 / (2 * np.pi))

def calculate_motor_torque(F_trac: float, r_w: float, G: float, eta_trans: float) -> float:
    """
    Convert tractive force to motor shaft torque.
    T_motor = (F_trac * r_w) / (G * eta_trans)
    """
    return (F_trac * r_w) / (G * eta_trans)

def get_motor_efficiency(T_motor: float, Omega_motor: float, eta_peak: float = 0.80) -> float:
    """
    Analytic representation of the 1418ZXF Geared BLDC motor map.
    Peak efficiency hits eta_peak (default 80%) near the rated speed of 450 RPM.
    """
    T_peak = 8.5
    RPM_peak = 450.0
    k1 = 0.005
    k2 = 5e-7
    
    eta = eta_peak - k1 * (T_motor - T_peak)**2 - k2 * (Omega_motor - RPM_peak)**2
    return max(0.1, min(eta_peak, eta))

def clamp_motor_rpm(Omega_motor: float, max_rpm: float) -> float:
    """Hard redline clamp limit on max motor RPM."""
    return min(Omega_motor, max_rpm)

def calculate_electrical_power(T_motor: float, Omega_motor: float, eta_peak: float = 0.80, is_propulsion: bool = True) -> float:
    """
    Calculate electrical power requirement from mechanical power and efficiency map.
    """
    eta_m = get_motor_efficiency(T_motor, Omega_motor, eta_peak)
    mechanical_power = T_motor * Omega_motor * (2 * np.pi / 60.0)
    
    if is_propulsion:
        return mechanical_power / eta_m
    else:
        # Regenerative braking case
        return mechanical_power * eta_m

def calculate_battery_state(P_elec: float, Voc: float, R_int: float) -> Tuple[float, float]:
    """
    Calculate terminal discharge voltage and current draw.
    I_batt = (Voc - sqrt(Voc^2 - 4 * R_int * P_elec)) / (2 * R_int)
    Vt = Voc - I_batt * R_int
    """
    det = Voc**2 - 4 * R_int * P_elec
    
    if det < 0:
        # Prevent math domain error for impossible power draw
        det = 0.0
        
    I_batt = (Voc - np.sqrt(det)) / (2 * R_int)
    Vt = Voc - I_batt * R_int
    
    return I_batt, Vt
