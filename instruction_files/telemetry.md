# FUTURE REAL-TIME TELEMETRY ARCHITECTURE & SENSOR SYSTEM SPECIFICATION

This document establishes the data validation standard for real-time telemetry processing, preparing the platform for live ingestion of vehicle state streams[cite: 2, 3].

---

## 1. Sensor Hierarchy, Communication Protocols, & Target Sampling Frequencies

The telemetry system must support data ingestion across a distributed network, matching the following sensor parameters[cite: 3]:

| Targeted Sensor System Component | Communication Protocol | Required Sampling Target | Strategic System Purpose |
| :--- | :--- | :--- | :--- |
| **Digital Shunt Power Meter (INA228)** | $I^2C$ Serial Interface[cite: 3] | $10 \text{ Hz}$[cite: 3] | Tracks instantaneous voltage, current, and electrical power consumption[cite: 3]. |
| **Wheel Encoder Sensors (Hall Effect)** | Edge Interrupts[cite: 3] | Event Triggered[cite: 3] | Measures wheel rotational velocity and tracks absolute lap distance metrics[cite: 3]. |
| **Powertrain Thermal Probes (Thermistors)** | Analog via ADC[cite: 3] | $50 \text{ Hz}$[cite: 3] | Monitors motor temperature to trigger safe thermal limits[cite: 3]. |
| **High-Precision Positioning (RTK-GPS)** | UART / NMEA Strings[cite: 3] | $5 \text{ Hz}$[cite: 3] | Provides sub-meter accuracy to track the vehicle's actual racing line[cite: 2, 3]. |
| **Inertial Measurement System (9x IMU)** | $I^2C$ / Matrix Stream[cite: 3] | $250 \text{ Hz}$[cite: 3] | Measures multi-axis acceleration and angular yaw velocity[cite: 2, 3]. |

---

## 2. Real-Time Ingestion Data Pipeline
[Raw Telemetry ASCII Stream Ingestion]
│
▼
[Verify Packet Integrity via Checksum Validation]
│
▼
[Extract Key Telemetry Metrics from JSON Struct Payloads]
│
▼
[Execute Extended Kalman Filter (EKF) Sensor Fusion]
│
▼
[Map Coordinates onto the Standardized S-Domain Track Layout]
│
▼
[Calculate Actual vs. Optimal Target Discrepancies]
│
▼
[Update Dashboard UI Visualizations & Driver Alerts]
## 3. EKF Sensor Fusion & Localization Specification
To ensure highly accurate tracking, raw data streams must be processed using a continuous Extended Kalman Filter (EKF)[cite: 3]. The filter handles sensor fusion across the following state variables:

$$\hat{x} = \begin{bmatrix} s & v & a & \beta_{\text{bias}} \end{bmatrix}^T$$

Where $s$ is the absolute spatial distance along the track path, $v$ is the longitudinal velocity, $a$ is the true acceleration, and $\beta_{\text{bias}}$ dynamically isolates sensor drift errors[cite: 3].

The filter resolves real-world sensor limitations through a dual verification approach:
*   High-frequency wheel encoder pulses and IMU acceleration inputs provide real-time state propagation[cite: 3].
*   Low-frequency GPS position and velocity tracking points correct for cumulative system integration drift[cite: 3].

This sensor fusion loop eliminates high-frequency noise and position errors caused by temporary satellite signal drops (e.g., driving under grandstands or bridges), ensuring the strategy optimization engine operates on clean, physically consistent state data[cite: 2, 3].
