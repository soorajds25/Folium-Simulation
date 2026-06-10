# MODULAR SYSTEM ARCHITECTURE & DATA PIPELINE SPECIFICATION

## 1. Modular Subsystem Layout
The framework architecture must decouple core physics tracking from frontend layout elements. It consists of seven distinct structural components:
[Track Ingestion Layer] (Reads Raw CSV/GPX/Manual Coordinates)
│
▼
[Normalized Track Database Model] (S-Domain Spatial Resolution Node Arrays)
│
▼
[Vehicle Dynamics Engine] (Computes Resistive Forces & Normal Load Balance)
│
▼
[Optimization Core Engine] (Executes Numerical Nonlinear Solvers)
│
▼
[Strategy Blueprint Vector Factory] (Converts Continuous Controls to Discrete Burst Schedules)
│
▼
[Real-Time Telemetry Pipeline] (Serial Message Stream Ingestion & EKF Data Fusion)
│
▼
[Analytical Frontend Render Interface] (High-Performance 60FPS Data Component Displays)
trict layout structured below to isolate business logic from presentation components:

```text
/strategy_platform
│
├── app.py                      # Main application bootstrap and layout manager
│
├── core/                       # Pure numerical operations modules (No Streamlit links)
│   ├── __init__.py
│   ├── track.py                # Normalized track spatial indexing and spline engines
│   ├── dynamics.py             # Longitudinal force dynamic profiling tools
│   ├── powertrain.py           # Battery internal resistance & motor map lookup components
│   └── optimizer.py            # Iterative optimization calculation cores
│
├── pipeline/                   # Real-time state telemetry tracking layers
│   ├── __init__.py
│   ├── serial_receiver.py      # Low-level JSON streaming state decoders
│   └── kalman_filter.py        # Fused sensor tracking state filters
│
└── ui/                         # Presentation layout component scripts
    ├── __init__.py
    ├── dashboard.py            # Streamlit primary dashboard view layout
    └── charts.py               # Analytical charting and plot configuration engines
3. Subsystem API Specifications & Inter-Module Payload Signatures
3.1 Track Representation Payload Signature (core/track.py)
Python
class NormalizedTrackNode:
    distance_m: float       # Arc length coordinate context s
    elevation_m: float      # Height tracking point above sea level H
    gradient_pct: float     # Path vertical grade derivative percent i
    curvature: float        # Lateral trajectory index parameter kappa
    corner_radius_m: float  # Radius parameter of localized bend curve
    track_width_m: float    # Absolute boundaries width of local racetrack corridor
3.2 Vehicle Control State Payload Signature (core/dynamics.py)
Python
class SystemStateVector:
    position_s: float       # Local position coordinate along tracking track (m)
    velocity_v: float       # Absolute vehicle velocity profile state (m/s)
    battery_soc: float      # Extracted charge balance status fraction [0.0, 1.0]
    cumulative_energy_j: float # Cumulative electrical energy used up to current node (J)
3.3 Core Optimization Solver Execution Signature (core/optimizer.py)
Python
def execute_trajectory_optimization(
    track_profile: list[NormalizedTrackNode], 
    vehicle_specs: dict, 
    max_lap_time_s: float
) -> list[SystemStateVector]:
    """
    Executes structural numerical trajectory generation.
    Must be completely free of Streamlit presentation dependencies.
    """
    pass
4. Recommended Implementation Order
Ensure core/track.py handles input standardization without truncation errors.

Build core/dynamics.py and validate total resistive calculations against baseline mathematical matrices.

Construct core/powertrain.py to correctly map battery parameters and handle 3D efficiency calculations.

Implement core/optimizer.py using vectorized steps to solve trajectory controls.

Create frontend elements (ui/) to display calculated strategy profiles.

Integrate telemetry parsing elements (pipeline/) to ingest real-time data.
