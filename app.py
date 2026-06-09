import streamlit as st
import os
import tempfile
import copy
from core.track import load_track
from core.optimizer import run_trajectory_optimization
from ui.dashboard import render_dashboard

def main():
    st.set_page_config(page_title="Shell Eco-Marathon Strategy Simulator", layout="wide")
    
    st.title("Professional Streamlit-Based Shell Eco-Marathon Vehicle Strategy Simulator")
    st.write("Welcome to the Optimization Dashboard. Please upload a track file (CSV or GPX) to begin.")
    
    uploaded_file = st.file_uploader("Upload Track Data", type=["csv", "gpx"])
    
    if uploaded_file is not None:
        try:
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
                tmp_file.write(uploaded_file.getbuffer())
                temp_path = tmp_file.name
            
            st.info(f"Processing track data from {uploaded_file.name}...")
            
            nodes = load_track(temp_path, track_width=5.0)
            st.success(f"Track processing complete! Generated {len(nodes)} normalized track nodes at 1-meter intervals.")
            
            if st.button("Run Trajectory Optimization"):
                with st.spinner("Executing Mathematical Solver Core over 4 laps (14.8 km)..."):
                    # Generate 4 Lap sequence 
                    multi_lap_nodes = []
                    base_dist = 0.0
                    
                    for lap in range(4):
                        for n in nodes:
                            new_node = copy.deepcopy(n)
                            new_node.distance_m += base_dist
                            multi_lap_nodes.append(new_node)
                        if len(multi_lap_nodes) > 0:
                            # Set offset for next lap
                            base_dist = multi_lap_nodes[-1].distance_m + 1.0 
                            
                    best_states, stats = run_trajectory_optimization(
                        multi_lap_nodes, 
                        target_time_s=2100.0  # 35 mins threshold
                    )
                    
                    # Render outputs dynamically
                    render_dashboard(multi_lap_nodes, best_states, stats)
                        
            os.remove(temp_path)
            
        except Exception as e:
            st.error(f"Error processing track: {e}")

if __name__ == "__main__":
    main()
