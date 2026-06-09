\# OPTIMIZATION ENGINE ARCHITECTURE \& SOLVER LOGIC SPECIFICATION



\## 1. Solver Architecture Evaluation

To pick the most appropriate strategy generation methodology, three mathematical control algorithms were evaluated:



| Optimization Methodology | Architectural Advantages | System Engineering Limitations |

| :--- | :--- | :--- |

| \*\*Dynamic Programming (DP)\*\* | Guarantees finding the global mathematical optimum; easily handles non-convex efficiency maps\[cite: 3]. | Vulnerable to the curse of dimensionality; calculation requirements scale exponentially with additional state states\[cite: 3]. |

| \*\*Model Predictive Control (MPC)\*\* | Provides excellent tracking error rejection under changing real-time wind or track grip conditions\[cite: 3]. | Prone to finding local minima if initial inputs are poor; higher calculation load per time step\[cite: 3]. |

| \*\*Iterative Linear Quadratic Regulator (iLQR)\*\* | Calculation requirements scale linearly ($O(N)$) over track distance nodes; handles complex constraints efficiently\[cite: 3]. | Requires a smooth, differentiable approximation of the motor map to ensure reliable gradient calculation\[cite: 3]. |



\### Selected Implementation Strategy:

The platform must utilize a \*\*hybrid optimization approach\*\*:

1\. An offline \*\*iLQR Core Solver Engine\*\* computes the baseline global strategy trajectory using smooth, continuous approximations of the motor efficiency maps\[cite: 3].

2\. A localized \*\*S-Domain Dynamic Programming (DP) Pipeline\*\* handles discrete switching options for the burst-coast schedules, avoiding issues with non-convex efficiency islands\[cite: 3].



\---



\## 2. State \& Control Boundary Mapping

Optimization variables must be strictly mapped using the following structural bounds\[cite: 3]:



\*   \*\*State Space Vectors ($X$):\*\*

&#x20;   $$X(s) = \\begin{bmatrix} v(s) \& E\_{\\text{electrical}}(s) \\end{bmatrix}^T$$

&#x20;   Where $v(s)$ is the vehicle longitudinal velocity ($\\text{m/s}$), and $E\_{\\text{electrical}}(s)$ tracks cumulative electrical energy used ($\\text{J}$)\[cite: 3].

\*   \*\*Control Input Vectors ($U$):\*\*

&#x20;   $$U(s) = \\begin{bmatrix} u(s) \\end{bmatrix} \\quad \\text{where } u(s) \\in \[0, 1] \\text{ (Continuous Throttle Scale)} \\text{\[cite: 3]}$$



\---



\## 3. Comprehensive Optimization Workflow Execution Path

The calculation pipeline must follow a strict, one-way sequence to ensure logical and physical consistency:



\[Standardized Track Node Database Ingestion]

│

▼

\[Calculate Curvature Acceleration \& Lateral Velocity Envelope Limits]

│

▼

\[Construct Dynamic Grid Boundaries (Eliminate Unfeasible State Space)]

│

▼

\[Execute Trajectory optimization Core Iterations]

│

▼

\[Extract Global Continuous Velocity Splines \& Throttle Demand Arrays]

│

▼

\[Apply Minimum Length Spatial Filters (Merge Chatter Into Human Repeatable Commands)]

│

▼

\[Output Autoritative Driver Strategy Blueprints]





