# SYSTEM DEVELOPMENT GUIDELINES & ARCHITECTURAL PRINCIPLES

## 1. Modular Architecture Principles
The platform must implement strict boundary separation between data transformation, physical state computation, and UI rendering. Under no circumstances should frontend components (Streamlit state keys or widget configurations) perform physical regressions, matrix cross-products, or numeric integration.

### Core Architecture Boundary Rules:
*   **Track Subsystem:** Reads geographical coordinates, filters elevation jitter, and outputs a one-dimensional array mapped purely to arc length ($s$).
*   **Vehicle Subsystem:** Encapsulates constants and vehicle configuration maps (e.g., torque maps, voltage levels, internal resistance coefficients). It exposes unified parameter-query functions to the physics engine.
*   **Optimization Engine:** Ingests the normalized track and vehicle representations, executes iterative numerical solvers, and outputs deterministic vectors of velocity, throttle, and energy targets.
*   **Visualization Layer:** Consumes static output vectors from the optimization engine and charts them. It must be decoupled from the numerical optimization lifecycle.

## 2. Coding Philosophy & Numeric Stability
*   **Vectorization:** Vectorized NumPy operations must be used for longitudinal state propagation over space loops to avoid execution bottlenecks.
*   **Data Types:** All spatial arrays, coordinate matrices, and energy states must use explicit floating-point sizes (e.g., 64-bit floats) to eliminate truncation errors during cumulative distance integration over long race distances.
*   **Exception Isolation:** Optimization solvers must gracefully catch divergence flags, low-rank constraints, or unfeasible boundary parameters, returning structural error payloads rather than raising platform-level exceptions that crash the dashboard interface.

## 3. Data Flow Architecture
The system must restrict data flows to a strictly linear path:
$$\text{Standardized Track Input} \longrightarrow \text{Physical Boundary Transformer} \longrightarrow \text{Solver Execution Framework} \longrightarrow \text{Render Engine}$$

To prevent data corruption, no downstream visualization widget may mutate arrays that reside in the application session states or optimization database caches.

## 4. Telemetry and Future Expansion Requirements
*   **Data Serialization:** The platform must use highly efficient formats (e.g., JSON payloads) for recording state streams, mirroring the low-level serial byte structures used by the event's official on-board telemetry networks.
*   **Low-Latency Processing:** State estimation pipelines must implement standalone filtering routines capable of processing high-frequency data inputs (e.g., IMU inputs at 250Hz and GPS tracking streams at 5Hz) to provide real-time updates for pit-wall analytics and driver path validation.