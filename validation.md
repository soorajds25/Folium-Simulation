# VEHICLE MODEL PARAMETER CALIBRATION & EMPIRICAL VALIDATION PROCEDURES

To verify simulator accuracy and prevent the optimization engine from exploiting unrealistic assumptions, the platform must implement empirical calibration routines using real-world telemetry data[cite: 3].

---

## 1. Empirical Derivation of Rolling Resistance ($C_{rr}$) via Coast-Down Segments

The platform must include a dedicated calibration routine that extracts the actual track rolling resistance coefficient directly from unguided coast-down data logs, isolating it from aerodynamic factors[cite: 3]:

### 1.1 Field Testing Procedure:
1. Accelerate the vehicle on a flat, straight section of the track until it reaches typical race cruise velocity[cite: 3].
2. Cut all power to the motor ($F_{\text{trac}} = 0$) and allow the car to coast naturally down to a low speed, ensuring no mechanical brakes are applied[cite: 3].
3. Capture the deceleration profile using high-resolution wheel encoder logs[cite: 3].

### 1.2 Mathematical Parameter Fitting:
During an unpowered coast-down on a flat surface, the vehicle's deceleration is governed solely by rolling resistance and aerodynamic drag[cite: 3, 9]:

$$M_v \cdot \delta \cdot \frac{dv}{dt} = - \left( M_v \cdot g \cdot C_{rr} + \frac{1}{2} \rho_a C_D A_f \cdot v^2 \right)$$

The calibration engine must use a non-linear least-squares regression algorithm to fit the logged velocity deceleration curve $(v, \frac{dv}{dt})$ against this model[cite: 3]. By targeting low-speed data points where aerodynamic drag forces are minimal, the system can cleanly isolate and calibrate the base rolling resistance parameter ($C_{rr}$) with high precision[cite: 3, 9].

---

## 2. Powertrain Residual Loss Modeling
Real-world drivetrains experience minor mechanical losses (e.g., chain misalignment, bearing drag, and tire deflection) that are difficult to model individually[cite: 3]. To account for this without overcomplicating the physics engine, the platform must implement a **Lumped Residual Force Loss Model** ($F_{\text{extra}}$)[cite: 3]:

$$F_{\text{extra}}(v) = F_0 + F_1 \cdot v$$

The parameters $F_0$ and $F_1$ are calculated by evaluating the difference between the electrical power input measured on track ($P_{\text{measured}}$) and the mechanical power output predicted by the baseline vehicle model ($P_{\text{predicted}}$) across steady-state runs[cite: 3]:

$$\Delta P_{\text{loss}}(s) = P_{\text{measured}}(s) - P_{\text{predicted}}(s)$$

The calibration module must fit these residual energy losses as an equivalent opposing force, embedding it directly into the primary longitudinal physics model[cite: 3]:

$$F_{\text{res\_total}} = F_w(v) + F_r(v) + F_g(s) + F_{\text{extra}}(v) \quad \text{[cite: 3, 9]}$$

This empirical calibration loop ensures the optimization engine generates strategies grounded in real-world vehicle performance, eliminating the risk of unrealistic efficiency predictions[cite: 3].