import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import streamlit as st
from typing import List
from core.dynamics import SystemStateVector
from core.track import NormalizedTrackNode

def render_race_charts(track_nodes: List[NormalizedTrackNode], optimized_states: List[SystemStateVector]):
    """
    Renders 6 high-contrast, distance-domain (s-domain) charts for race engineers.
    """
    sns.set_theme(style="darkgrid")
    
    s = np.array([state.position_s for state in optimized_states])
    v = np.array([state.velocity_v for state in optimized_states])
    throttle = np.array([state.throttle_u for state in optimized_states])
    power = np.array([state.power_elec_w for state in optimized_states])
    current = np.array([state.current_batt_a for state in optimized_states])
    eta = np.array([state.motor_efficiency for state in optimized_states])
    soc = np.array([state.battery_soc for state in optimized_states]) * 100.0
    
    ele = np.array([node.elevation_m for node in track_nodes])
    grad = np.array([node.gradient_pct for node in track_nodes])
    
    # Calculate v_bound roughly for visual context
    g = 9.81
    mu_lat = 1.0
    v_bounds = []
    for node in track_nodes:
        if node.curvature <= 1e-6:
            v_bounds.append(60.0) # Arbitrary max for plot
        else:
            v_bounds.append(np.sqrt((mu_lat * g) / node.curvature))
    v_bound = np.clip(np.array(v_bounds), 0.0, 60.0)
    
    # Chart A: Speed Profile
    figA, axA = plt.subplots(figsize=(10, 3))
    axA.plot(s, v, label='Vehicle Speed (m/s)', color='#1f77b4', linewidth=2)
    axA.plot(s, v_bound, label='Lateral Grip Limit', color='#d62728', linestyle='--', alpha=0.7)
    axA.set_title("A. Speed Profile vs Cornering Boundaries", fontweight='bold')
    axA.set_xlabel("Distance (m)")
    axA.set_ylabel("Velocity (m/s)")
    axA.set_xlim(s[0], s[-1])
    axA.legend()
    st.pyplot(figA)
    
    # Chart B: Throttle Input
    figB, axB = plt.subplots(figsize=(10, 2))
    axB.fill_between(s, 0, throttle, color='#2ca02c', alpha=0.6)
    axB.set_title("B. Throttle Input Profile (Burst / Coast)", fontweight='bold')
    axB.set_xlabel("Distance (m)")
    axB.set_ylabel("Throttle Input")
    axB.set_yticks([0, 1])
    axB.set_yticklabels(['Coast', 'Burst'])
    axB.set_xlim(s[0], s[-1])
    st.pyplot(figB)
    
    # Chart C: Electrical Power & Current
    figC, axC1 = plt.subplots(figsize=(10, 3))
    axC2 = axC1.twinx()
    axC1.plot(s, power, color='#ff7f0e', label='Power (W)', alpha=0.8)
    axC2.plot(s, current, color='#9467bd', label='Current (A)', alpha=0.8, linestyle=':')
    axC1.set_title("C. Electrical Power & Current Draw", fontweight='bold')
    axC1.set_xlabel("Distance (m)")
    axC1.set_ylabel("Power (W)", color='#ff7f0e')
    axC2.set_ylabel("Current (A)", color='#9467bd')
    axC1.set_xlim(s[0], s[-1])
    lines1, labels1 = axC1.get_legend_handles_labels()
    lines2, labels2 = axC2.get_legend_handles_labels()
    axC1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    st.pyplot(figC)
    
    # Chart D: Motor Efficiency
    figD, axD = plt.subplots(figsize=(10, 2.5))
    axD.scatter(s[throttle > 0], eta[throttle > 0] * 100.0, s=2, color='#17becf', alpha=0.5)
    axD.set_title("D. Motor Efficiency Tracking (Active Zones)", fontweight='bold')
    axD.set_xlabel("Distance (m)")
    axD.set_ylabel("Efficiency (%)")
    axD.set_ylim(0, 100)
    axD.set_xlim(s[0], s[-1])
    st.pyplot(figD)
    
    # Chart E: Battery SOC
    figE, axE = plt.subplots(figsize=(10, 2.5))
    axE.plot(s, soc, color='#bcbd22', linewidth=2)
    axE.set_title("E. Battery State of Charge Depletion", fontweight='bold')
    axE.set_xlabel("Distance (m)")
    axE.set_ylabel("SOC (%)")
    axE.set_xlim(s[0], s[-1])
    st.pyplot(figE)
    
    # Chart F: Track Topography
    figF, axF1 = plt.subplots(figsize=(10, 3))
    axF2 = axF1.twinx()
    axF1.plot(s, ele, color='#8c564b', label='Elevation (m)')
    axF2.fill_between(s, 0, grad, color='#7f7f7f', alpha=0.3, label='Gradient (%)')
    axF1.set_title("F. Track Topography Contextualization", fontweight='bold')
    axF1.set_xlabel("Distance (m)")
    axF1.set_ylabel("Elevation (m)", color='#8c564b')
    axF2.set_ylabel("Gradient (%)", color='#7f7f7f')
    axF1.set_xlim(s[0], s[-1])
    lines_f1, labels_f1 = axF1.get_legend_handles_labels()
    lines_f2, labels_f2 = axF2.get_legend_handles_labels()
    axF1.legend(lines_f1 + lines_f2, labels_f1 + labels_f2, loc='upper right')
    st.pyplot(figF)
