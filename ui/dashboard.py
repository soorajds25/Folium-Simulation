import streamlit as st
from typing import List, Dict, Any
from core.track import NormalizedTrackNode
from core.dynamics import SystemStateVector
from ui.charts import render_race_charts


def render_sidebar_params() -> Dict[str, Any]:
    """
    Renders the hardware parameter sidebar with 4 collapsible expanders.
    Returns a vehicle_params dictionary with all widget values bundled.
    """
    st.sidebar.markdown("## ⚙️ Digital Twin Parameters")
    st.sidebar.markdown(
        "<small>Adjust hardware specs below. Press **Run Trajectory Optimization** "
        "to apply changes and recalculate the strategy.</small>",
        unsafe_allow_html=True
    )
    st.sidebar.markdown("---")

    # ── Expander 1: Chassis & Aerodynamics ───────────────────────────────────
    with st.sidebar.expander("🚗 Chassis & Aerodynamics", expanded=True):
        st.markdown("**Kenaf Fibre Composite Frame**")
        M_v = st.number_input(
            "Total Vehicle + Rider Mass (kg)",
            min_value=50.0, max_value=200.0,
            value=110.0, step=0.5,
            key="mass_input",
            help="Combined mass of chassis, rider, battery, and all components."
        )
        Cd = st.number_input(
            "Aerodynamic Drag Coefficient (Cd)",
            min_value=0.1, max_value=1.5,
            value=0.332, step=0.001, format="%.3f",
            key="cd_input",
            help="Drag coefficient of the vehicle body shell."
        )
        A = st.number_input(
            "Frontal Area (A) [m²]",
            min_value=0.1, max_value=2.0,
            value=0.388, step=0.001, format="%.3f",
            key="area_input",
            help="Projected frontal cross-section area in m²."
        )
        Crr = st.number_input(
            "Tyre Rolling Resistance (Crr)",
            min_value=0.001, max_value=0.050,
            value=0.005, step=0.0005, format="%.4f",
            key="crr_input",
            help="Rolling resistance coefficient. Ralson 24\" front / Speedways Commando 20\" rear."
        )
        # Derived value display
        cd_af = Cd * A
        st.info(f"**CdA product:** `{cd_af:.4f} m²` (Cd × A)")

    # ── Expander 2: Motor & Drivetrain ───────────────────────────────────────
    with st.sidebar.expander("⚡ Motor & Drivetrain", expanded=True):
        st.markdown("**1418ZXF Geared BLDC · 48V / 500W**")
        st.markdown(
            "Rated Speed: 450 RPM | No-Load: 516 RPM | "
            "Internal Gear Ratio: **1:6**",
        )
        eta_motor_peak = st.slider(
            "Motor Peak Efficiency (%)",
            min_value=50.0, max_value=95.0,
            value=80.0, step=0.5,
            key="eta_motor_input",
            help="Peak efficiency of the 1418ZXF motor at optimal torque/RPM band."
        )
        eta_trans = st.slider(
            "Drivetrain Mechanical Efficiency (%)",
            min_value=70.0, max_value=100.0,
            value=98.0, step=0.5,
            key="eta_trans_input",
            help="Mechanical transmission efficiency including chain/belt losses."
        )
        r_w = st.number_input(
            "Driven Wheel Effective Radius (m)",
            min_value=0.10, max_value=0.50,
            value=0.254, step=0.001, format="%.3f",
            key="rw_input",
            help="Effective rolling radius of the driven rear wheel (Speedways Commando 20\")."
        )
        G = st.number_input(
            "Internal Gear Reduction Ratio",
            min_value=1.0, max_value=20.0,
            value=6.0, step=0.5, format="%.1f",
            key="gear_ratio_input",
            help="Total gear reduction from motor shaft to wheel axle. 1418ZXF = 1:6."
        )

    # ── Expander 3: Battery Constraints ──────────────────────────────────────
    with st.sidebar.expander("🔋 Battery Constraints", expanded=True):
        st.markdown("**YB-ZB-13S7P · 13S7P Li-ion**")
        Voc = st.number_input(
            "Nominal Open-Circuit Voltage (V)",
            min_value=10.0, max_value=60.0,
            value=48.0, step=0.1, format="%.1f",
            key="voc_input",
            help="Nominal battery pack voltage (48V nominal for 13S Li-ion configuration)."
        )
        V_min = st.number_input(
            "Minimum Operating Voltage (V)",
            min_value=10.0, max_value=59.0,
            value=37.7, step=0.1, format="%.1f",
            key="vmin_input",
            help="BMS low-voltage cutoff. 13S7P Li-ion = 37.7V (2.9V per cell)."
        )
        V_max = st.number_input(
            "Maximum Charging Voltage (V)",
            min_value=V_min + 0.1, max_value=60.0,
            value=54.6, step=0.1, format="%.1f",
            key="vmax_input",
            help="BMS charge cutoff. 13S7P Li-ion = 54.6V (4.2V per cell)."
        )
        I_max = st.number_input(
            "BMS Max Continuous Current (A)",
            min_value=1.0, max_value=100.0,
            value=20.0, step=0.5, format="%.1f",
            key="imax_input",
            help="Maximum continuous discharge current enforced by the BMS."
        )
        # Display computed power cap
        P_cap = Voc * I_max
        st.info(f"**Peak Power Cap:** `{P_cap:.0f} W` (Voc × I_max)")

    # ── Expander 4: Competition Constraints ───────────────────────────────────
    with st.sidebar.expander("🏁 Competition Constraints", expanded=False):
        st.markdown("**Shell Eco-Marathon · 4 Laps · 14.8 km**")
        target_time_s = st.number_input(
            "Target Total Lap Time (seconds)",
            min_value=600, max_value=3600,
            value=2100, step=30,
            key="target_time_input",
            help="Maximum permissible race time. Shell Eco-Marathon limit = 2100s (35 min)."
        )
        st.markdown(f"⏱️ **{target_time_s / 60:.1f} minutes** ({target_time_s} s)")

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "<small>🔒 **15m Burst / 40m Coast** spatial hysteresis active.<br>"
        "🔒 Topography hill-alignment override active.</small>",
        unsafe_allow_html=True
    )

    # Bundle all values into the unified vehicle_params dictionary
    vehicle_params = {
        'M_v': M_v,
        'Cd': Cd,
        'A': A,
        'Crr': Crr,
        'eta_motor_peak': eta_motor_peak,
        'eta_trans': eta_trans,
        'r_w': r_w,
        'G': G,
        'Voc': Voc,
        'V_min': V_min,
        'V_max': V_max,
        'I_max': I_max,
        'target_time_s': int(target_time_s)
    }
    return vehicle_params


def render_dashboard(
    track_nodes: List[NormalizedTrackNode],
    optimized_states: List[SystemStateVector],
    stats: Dict[str, Any],
    vehicle_params: Dict[str, Any]
):
    """
    Dynamic Racing Engine Dashboard layout.
    Renders KPI metrics, parameter summary, and all telemetry charts.
    """
    st.markdown("---")

    # ── KPI Metric Tiles ─────────────────────────────────────────────────────
    col1, col2, col3, col4, col5 = st.columns(5)

    lap_time  = stats.get('time_s', 0.0)
    energy    = stats.get('energy_j', 0.0)
    eff       = stats.get('efficiency_km_kwh', 0.0)
    total_dist_km = track_nodes[-1].distance_m / 1000.0 if track_nodes else 1.0
    wh_km     = (energy / 3600.0) / total_dist_km if total_dist_km > 0 else 0.0
    transitions = stats.get('transitions', 0)

    col1.metric(
        label="Total Lap Time",
        value=f"{lap_time / 60.0:.2f} min",
        delta=f"{lap_time:.0f} s",
        delta_color="off"
    )
    col2.metric(
        label="Total Energy Used",
        value=f"{energy / 1000.0:.1f} kJ",
        delta=f"{energy / 3600.0:.1f} Wh",
        delta_color="inverse"
    )
    col3.metric(label="System Efficiency", value=f"{eff:.2f} km/kWh")
    col4.metric(
        label="Consumption Rate",
        value=f"{wh_km:.2f} Wh/km",
        delta_color="inverse"
    )
    col5.metric(label="Burst/Coast Transitions", value=f"{transitions}")

    if 'warning' in stats:
        st.warning(f"⚠️ Solver Warning: {stats['warning']}")

    # ── Active Hardware Config Summary ────────────────────────────────────────
    with st.expander("📋 Active Vehicle Configuration (Digital Twin Snapshot)", expanded=False):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown("**Chassis & Aero**")
            st.markdown(f"- Mass: `{vehicle_params['M_v']} kg`")
            st.markdown(f"- Cd: `{vehicle_params['Cd']}`")
            st.markdown(f"- Area: `{vehicle_params['A']} m²`")
            st.markdown(f"- CdA: `{vehicle_params['Cd'] * vehicle_params['A']:.4f} m²`")
            st.markdown(f"- Crr: `{vehicle_params['Crr']}`")
        with c2:
            st.markdown("**Motor & Drivetrain**")
            st.markdown(f"- Motor Peak η: `{vehicle_params['eta_motor_peak']}%`")
            st.markdown(f"- Trans. η: `{vehicle_params['eta_trans']}%`")
            st.markdown(f"- Wheel Radius: `{vehicle_params['r_w']} m`")
            st.markdown(f"- Gear Ratio: `1:{vehicle_params['G']:.0f}`")
        with c3:
            st.markdown("**Battery (YB-ZB-13S7P)**")
            st.markdown(f"- Voc: `{vehicle_params['Voc']} V`")
            st.markdown(f"- V Range: `{vehicle_params['V_min']}V – {vehicle_params['V_max']}V`")
            st.markdown(f"- I Max: `{vehicle_params['I_max']} A`")
            st.markdown(f"- P Cap: `{vehicle_params['Voc'] * vehicle_params['I_max']:.0f} W`")
        with c4:
            st.markdown("**Competition**")
            st.markdown(f"- Target Time: `{vehicle_params['target_time_s']} s`")
            st.markdown(f"- ({vehicle_params['target_time_s'] / 60:.1f} min)")
            st.markdown(f"- Distance: `{total_dist_km:.2f} km`")
            st.markdown(f"- Opt Speed: `{stats.get('target_speed', 0):.2f} m/s`")

    st.markdown("---")

    # ── Chart Tabs ────────────────────────────────────────────────────────────
    tab1, tab2 = st.tabs(["🏎️ Race Strategy Profile", "🗺️ Track Dynamics"])

    with tab1:
        st.subheader("Spatial Control Strategy Vectors")
        render_race_charts(track_nodes, optimized_states)

    with tab2:
        st.subheader("Track Geometric Properties")
        st.write(f"**Total distance integrated:** {track_nodes[-1].distance_m / 1000.0:.3f} km")
        st.write(f"**Maximum gradient encountered:** {max(n.gradient_pct for n in track_nodes):.2f} %")
        min_radius = min(n.corner_radius_m for n in track_nodes)
        if min_radius == float('inf'):
            st.write("**Minimum corner radius:** ∞ m (straight track)")
        else:
            st.write(f"**Minimum corner radius:** {min_radius:.1f} m")
