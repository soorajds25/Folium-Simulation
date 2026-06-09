import streamlit as st
import os
import tempfile
import copy
from core.track import load_track
from core.optimizer import run_trajectory_optimization
from ui.dashboard import render_sidebar_params, render_dashboard

st.set_page_config(
    page_title="Shell Eco-Marathon Strategy Simulator",
    page_icon="🏎️",
    layout="wide"
)

def main():
    # ── Sidebar: Render hardware parameter widgets ─────────────────────────
    # vehicle_params is always collected from the sidebar so Streamlit keeps
    # widget state live. The heavy optimization only runs on button click.
    vehicle_params = render_sidebar_params()

    # ── Main header ────────────────────────────────────────────────────────
    st.title("🏎️ Shell Eco-Marathon Vehicle Strategy Simulator")
    st.markdown(
        "Professional distance-domain trajectory optimizer with **Digital Twin** "
        "hardware parameterization. Upload a track file (CSV or GPX) to begin."
    )

    # ── Track file uploader ────────────────────────────────────────────────
    uploaded_file = st.file_uploader(
        "📂 Upload Track Data File",
        type=["csv", "gpx"],
        help="Accepts pre-computed CSV nodes or raw GPX coordinate files."
    )

    if uploaded_file is not None:
        try:
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_file:
                tmp_file.write(uploaded_file.getbuffer())
                temp_path = tmp_file.name

            st.info(f"🔄 Processing track data from **{uploaded_file.name}**…")
            nodes = load_track(temp_path, track_width=5.0)
            st.success(
                f"✅ Track ingestion complete — "
                f"**{len(nodes):,}** normalized nodes at 1-metre intervals."
            )

            # ── Optimizer trigger (button-gated to protect CPU) ────────────
            st.markdown("---")
            col_btn, col_info = st.columns([1, 3])
            with col_btn:
                run_clicked = st.button(
                    "🚀 Run Trajectory Optimization",
                    use_container_width=True,
                    type="primary"
                )
            with col_info:
                st.markdown(
                    f"**Active config:** Mass `{vehicle_params['M_v']} kg` · "
                    f"CdA `{vehicle_params['Cd'] * vehicle_params['A']:.4f} m²` · "
                    f"Crr `{vehicle_params['Crr']}` · "
                    f"Motor η `{vehicle_params['eta_motor_peak']}%` · "
                    f"Target `{vehicle_params['target_time_s'] / 60:.1f} min`"
                )

            if run_clicked:
                with st.spinner(
                    "⚙️ Executing Mathematical Solver Core over 4 laps (14.8 km)…"
                ):
                    # Build 4-lap node sequence
                    multi_lap_nodes = []
                    base_dist = 0.0
                    for lap in range(4):
                        for n in nodes:
                            new_node = copy.deepcopy(n)
                            new_node.distance_m += base_dist
                            multi_lap_nodes.append(new_node)
                        if multi_lap_nodes:
                            base_dist = multi_lap_nodes[-1].distance_m + 1.0

                    # Pass the full vehicle_params dictionary into the solver
                    best_states, stats = run_trajectory_optimization(
                        multi_lap_nodes,
                        vehicle_params=vehicle_params
                    )

                # Render the dashboard with results + active hardware snapshot
                render_dashboard(multi_lap_nodes, best_states, stats, vehicle_params)

            # Clean up temp file
            try:
                os.remove(temp_path)
            except OSError:
                pass

        except Exception as e:
            st.error(f"❌ Error processing track: {e}")
            raise

if __name__ == "__main__":
    main()
