# HARDWARE-IN-THE-LOOP AND REAL-TIME TELEMETRY DEVELOPMENT ROADMAP

## Phase 1: Core Architecture Validation (Weeks 1-2)
*   Establish and validate the standardized distance-domain spline transformation engine (`core/track.py`).
*   Implement baseline longitudinal force equations and verify rolling, aerodynamic, and gradient force calculations against known reference datasets.

## Phase 2: Powertrain & Battery Modeling (Weeks 3-4)
*   Integrate 3D motor efficiency map interpolation matrices.
*   Implement the battery equivalent-circuit internal resistance model and validate state-of-charge calculations.

## Phase 3: Trajectory Optimization Core (Weeks 5-6)
*   Develop the primary trajectory optimization engine using continuous solvers.
*   Implement curvature-based lateral velocity limits and establish structural constraint verification routines.

## Phase 4: Strategy Blueprint Processing (Week 7)
*   Develop spatial hysteresis filtering tools to convert raw optimization traces into human-repeatable burst-coast schedules.
*   Implement time-weighting tuning logic to tightly target race time thresholds.

## Phase 5: Dashboard Visualization (Week 8)
*   Build the Streamlit analytical interface layout.
*   Render distance-synchronized performance charts and integrate metric tracking indicators.

## Phase 6: Telemetry Pipeline Prep (Week 9)
*   Develop low-level telemetry streaming data packet structures.
*   Implement and validate the Extended Kalman Filter (EKF) sensor-fusion tracking equations.

## Phase 7: System Calibration Modules (Week 10)
*   Build empirical calibration routines to extract rolling resistance parameters from coast-down log files.
*   Integrate lumped residual loss calculation engines to continuously refine model accuracy.