import streamlit as st
from typing import List, Dict, Any
from core.track import NormalizedTrackNode
from core.dynamics import SystemStateVector
from ui.charts import render_race_charts

def render_dashboard(track_nodes: List[NormalizedTrackNode], optimized_states: List[SystemStateVector], stats: Dict[str, Any]):
    """
    Dynamic Racing Engine Dashboard layout.
    """
    st.markdown("---")
    
    # High-impact metric boxes
    col1, col2, col3, col4, col5 = st.columns(5)
    
    lap_time = stats.get('time_s', 0.0)
    energy = stats.get('energy_j', 0.0)
    eff = stats.get('efficiency_km_kwh', 0.0)
    total_dist_km = track_nodes[-1].distance_m / 1000.0 if len(track_nodes) > 0 else 1.0
    wh_km = (energy / 3600.0) / total_dist_km if total_dist_km > 0 else 0.0
    transitions = stats.get('transitions', 0)
    
    col1.metric(label="Total Lap Time", value=f"{lap_time/60.0:.2f} min", delta=f"{lap_time:.0f} s", delta_color="off")
    col2.metric(label="Total Energy", value=f"{energy/1000.0:.1f} kJ", delta=f"{energy/3600.0:.1f} Wh", delta_color="inverse")
    col3.metric(label="System Efficiency", value=f"{eff:.2f} km/kWh")
    col4.metric(label="Consumption Rate", value=f"{wh_km:.2f} Wh/km", delta_color="inverse")
    col5.metric(label="Burst/Coast Transitions", value=f"{transitions}")
    
    if 'warning' in stats:
        st.warning(f"Solver Warning: {stats['warning']}")
        
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["🏎️ Race Strategy Profile", "🗺️ Track Dynamics"])
    
    with tab1:
        st.subheader("Spatial Control Strategy Vectors")
        render_race_charts(track_nodes, optimized_states)
        
    with tab2:
        st.subheader("Track Geometric Properties")
        st.write(f"**Total distance integrated:** {track_nodes[-1].distance_m:.1f} meters")
        st.write(f"**Maximum gradient encountered:** {max([n.gradient_pct for n in track_nodes]):.1f}%")
        st.write(f"**Minimum corner radius:** {min([n.corner_radius_m for n in track_nodes]):.1f} meters")
