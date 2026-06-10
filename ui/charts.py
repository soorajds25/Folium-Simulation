import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import streamlit as st
from typing import List
from core.dynamics import SystemStateVector
from core.track import NormalizedTrackNode

# ── Shared layout configuration for oscilloscope-style deep zoom ──────────
_CHART_TEMPLATE = "plotly_dark"
_GRID_COLOR = "rgba(255,255,255,0.08)"
_HOVER_MODE = "x unified"

def _base_layout(**overrides) -> dict:
    """Shared layout kwargs for every chart — dark theme, deep-zoom enabled."""
    defaults = dict(
        template=_CHART_TEMPLATE,
        height=300,
        margin=dict(l=60, r=30, t=40, b=40),
        hovermode=_HOVER_MODE,
        dragmode="zoom",          # default interaction = rectangle zoom
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="right", x=1, font=dict(size=11)
        ),
        xaxis=dict(
            showgrid=True, gridcolor=_GRID_COLOR,
            showspikes=True, spikemode="across",
            spikethickness=1, spikecolor="rgba(255,255,255,0.3)",
            title="Distance (km)",
            rangeslider=dict(visible=False),
            # Dynamic grid subdivisions when zooming
            dtick=None,           # auto-subdivide
            minor=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)", dtick=None),
        ),
        yaxis=dict(
            showgrid=True, gridcolor=_GRID_COLOR,
            minor=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)"),
        ),
    )
    defaults.update(overrides)
    return defaults


def render_race_charts(
    track_nodes: List[NormalizedTrackNode],
    optimized_states: List[SystemStateVector]
):
    """
    Renders 6 interactive Plotly charts with oscilloscope-style deep zoom,
    hover tooltips, and dynamic grid subdivisions.
    """
    # ── Extract telemetry arrays ──────────────────────────────────────────
    s     = np.array([st_.position_s for st_ in optimized_states])
    s_km  = s / 1000.0

    v        = np.array([st_.velocity_v   for st_ in optimized_states])
    throttle = np.array([st_.throttle_u   for st_ in optimized_states])
    power    = np.array([st_.power_elec_w for st_ in optimized_states])
    current  = np.array([st_.current_batt_a for st_ in optimized_states])
    eta      = np.array([st_.motor_efficiency for st_ in optimized_states])
    soc      = np.array([st_.battery_soc for st_ in optimized_states]) * 100.0

    # Track topology arrays
    track_s    = np.array([n.distance_m    for n in track_nodes])
    track_s_km = track_s / 1000.0
    ele        = np.array([n.elevation_m   for n in track_nodes])
    grad       = np.array([n.gradient_pct  for n in track_nodes])

    # Lateral grip velocity ceiling (visual context only)
    g = 9.81
    mu_lat = 1.0
    v_bounds = np.array([
        60.0 if n.curvature <= 1e-6 else np.sqrt((mu_lat * g) / n.curvature)
        for n in track_nodes
    ])
    v_bound = np.clip(v_bounds, 0.0, 60.0)

    # ── CHART A: Speed Profile vs Cornering Boundaries ────────────────────
    figA = go.Figure()
    figA.add_trace(go.Scatter(
        x=s_km, y=v, mode='lines',
        name='Vehicle Speed (m/s)',
        line=dict(color='#4fc3f7', width=2),
        hovertemplate='%{x:.3f} km<br>Speed: %{y:.2f} m/s<extra></extra>'
    ))
    figA.add_trace(go.Scatter(
        x=track_s_km, y=v_bound, mode='lines',
        name='Lateral Grip Limit',
        line=dict(color='#ef5350', width=1.5, dash='dash'),
        opacity=0.7,
        hovertemplate='%{x:.3f} km<br>Grip Limit: %{y:.1f} m/s<extra></extra>'
    ))
    figA.update_layout(
        **_base_layout(
            title=dict(text="A. Speed Profile vs Cornering Boundaries", font=dict(size=14)),
            yaxis_title="Velocity (m/s)",
        )
    )
    st.plotly_chart(figA, use_container_width=True, key="chart_a")

    # ── CHART B: Throttle Input Profile (Burst / Coast) ───────────────────
    figB = go.Figure()
    figB.add_trace(go.Scatter(
        x=s_km, y=throttle, mode='lines',
        name='Throttle Input',
        fill='tozeroy',
        line=dict(color='#66bb6a', width=1),
        fillcolor='rgba(102,187,106,0.4)',
        hovertemplate='%{x:.3f} km<br>Throttle: %{y}<extra></extra>'
    ))
    figB.update_layout(
        **_base_layout(
            title=dict(text="B. Throttle Input Profile (Burst / Coast)", font=dict(size=14)),
            height=220,
            yaxis=dict(
                showgrid=True, gridcolor=_GRID_COLOR,
                tickvals=[0, 1], ticktext=['Coast', 'Burst'],
                range=[-0.05, 1.15],
                title="",
            ),
        )
    )
    st.plotly_chart(figB, use_container_width=True, key="chart_b")

    # ── CHART C: Electrical Power & Current Draw ──────────────────────────
    figC = make_subplots(specs=[[{"secondary_y": True}]])
    figC.add_trace(go.Scatter(
        x=s_km, y=power, mode='lines',
        name='Power (W)',
        line=dict(color='#ffa726', width=2),
        hovertemplate='%{x:.3f} km<br>Power: %{y:.1f} W<extra></extra>'
    ), secondary_y=False)
    figC.add_trace(go.Scatter(
        x=s_km, y=current, mode='lines',
        name='Current (A)',
        line=dict(color='#ab47bc', width=1.5, dash='dot'),
        opacity=0.85,
        hovertemplate='%{x:.3f} km<br>Current: %{y:.2f} A<extra></extra>'
    ), secondary_y=True)
    figC.update_layout(
        **_base_layout(
            title=dict(text="C. Electrical Power & Current Draw", font=dict(size=14)),
        )
    )
    figC.update_yaxes(
        title_text="Power (W)", title_font_color='#ffa726',
        showgrid=True, gridcolor=_GRID_COLOR,
        secondary_y=False
    )
    figC.update_yaxes(
        title_text="Current (A)", title_font_color='#ab47bc',
        showgrid=False,
        secondary_y=True
    )
    st.plotly_chart(figC, use_container_width=True, key="chart_c")

    # ── CHART D: Motor Efficiency Tracking (Active Zones) ─────────────────
    active_mask = throttle > 0
    figD = go.Figure()
    if np.any(active_mask):
        figD.add_trace(go.Scattergl(
            x=s_km[active_mask],
            y=eta[active_mask] * 100.0,
            mode='markers',
            name='Motor η (%)',
            marker=dict(color='#26c6da', size=3, opacity=0.5),
            hovertemplate='%{x:.3f} km<br>η: %{y:.1f}%<extra></extra>'
        ))
    figD.update_layout(
        **_base_layout(
            title=dict(text="D. Motor Efficiency Tracking (Active Zones)", font=dict(size=14)),
            height=260,
            yaxis=dict(
                showgrid=True, gridcolor=_GRID_COLOR,
                range=[0, 100], title="Efficiency (%)",
                minor=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)"),
            ),
        )
    )
    st.plotly_chart(figD, use_container_width=True, key="chart_d")

    # ── CHART E: Battery State of Charge Depletion ────────────────────────
    figE = go.Figure()
    figE.add_trace(go.Scatter(
        x=s_km, y=soc, mode='lines',
        name='SOC (%)',
        line=dict(color='#c0ca33', width=2.5),
        hovertemplate='%{x:.3f} km<br>SOC: %{y:.2f}%<extra></extra>'
    ))
    figE.update_layout(
        **_base_layout(
            title=dict(text="E. Battery State of Charge Depletion", font=dict(size=14)),
            height=260,
            yaxis_title="SOC (%)",
        )
    )
    st.plotly_chart(figE, use_container_width=True, key="chart_e")

    # ── CHART F: Track Topography Contextualization ───────────────────────
    figF = make_subplots(specs=[[{"secondary_y": True}]])
    figF.add_trace(go.Scatter(
        x=track_s_km, y=ele, mode='lines',
        name='Elevation (m)',
        line=dict(color='#8d6e63', width=2),
        hovertemplate='%{x:.3f} km<br>Elevation: %{y:.1f} m<extra></extra>'
    ), secondary_y=False)
    figF.add_trace(go.Scatter(
        x=track_s_km, y=grad, mode='lines',
        name='Gradient (%)',
        fill='tozeroy',
        line=dict(color='#bdbdbd', width=0.5),
        fillcolor='rgba(189,189,189,0.2)',
        hovertemplate='%{x:.3f} km<br>Gradient: %{y:.2f}%<extra></extra>'
    ), secondary_y=True)
    figF.update_layout(
        **_base_layout(
            title=dict(text="F. Track Topography Contextualization", font=dict(size=14)),
        )
    )
    figF.update_yaxes(
        title_text="Elevation (m)", title_font_color='#8d6e63',
        showgrid=True, gridcolor=_GRID_COLOR,
        secondary_y=False
    )
    figF.update_yaxes(
        title_text="Gradient (%)", title_font_color='#bdbdbd',
        showgrid=False,
        secondary_y=True
    )
    st.plotly_chart(figF, use_container_width=True, key="chart_f")
