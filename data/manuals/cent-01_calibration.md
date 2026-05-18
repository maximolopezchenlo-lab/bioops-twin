# CENT-01 Laboratory Centrifuge Calibration and Operation Manual

## 1. Introduction
The CENT-01 is a high-speed, precision laboratory centrifuge designed for biological sample separation. This manual covers the standard operating procedures, calibration protocols, and safety limits for the CENT-01 model. 

## 2. General Operation
To ensure safety and equipment longevity, operators must adhere to strict payload-to-RPM ratios. Excessive RPM on heavy payloads can cause severe resonant vibration, potentially leading to catastrophic hardware failure or sample destruction. 
The device supports a maximum theoretical rotational speed of 15,000 RPM under zero-load conditions.

## 3. Calibration Tables
The following tables outline the maximum safe RPM and expected vibration (RMS g-force) limits based on the payload mass. 

### 3.1. Standard Rotor Calibration

| Payload Mass (g) | Max Safe RPM | Warning Vibration Limit (g) | Critical Shutdown Limit (g) |
|------------------|--------------|-----------------------------|-----------------------------|
| 10g              | 12,000 RPM   | 0.25 g                      | 0.50 g                      |
| 50g              | 8,000 RPM    | 0.30 g                      | 0.60 g                      |
| 100g             | 5,000 RPM    | 0.35 g                      | 0.70 g                      |
| 250g             | 3,000 RPM    | 0.40 g                      | 0.80 g                      |
| 500g             | 1,500 RPM    | 0.50 g                      | 1.00 g                      |

### 3.2. Heavy Duty Rotor Calibration

| Payload Mass (g) | Max Safe RPM | Warning Vibration Limit (g) | Critical Shutdown Limit (g) |
|------------------|--------------|-----------------------------|-----------------------------|
| 100g             | 7,000 RPM    | 0.30 g                      | 0.65 g                      |
| 250g             | 4,500 RPM    | 0.35 g                      | 0.75 g                      |
| 500g             | 2,500 RPM    | 0.40 g                      | 0.85 g                      |
| 1000g            | 1,000 RPM    | 0.55 g                      | 1.10 g                      |

## 4. Emergency Procedures
If the telemetry system detects a vibration exceeding the Critical Shutdown Limit, the centrifuge will automatically engage the EMERGENCY_STOP protocol.
- **Rule 4.A**: Under no circumstances should an operator attempt to override an EMERGENCY_STOP.
- **Rule 4.B**: After an EMERGENCY_STOP, the centrifuge requires a full mechanical reset and recalibration before the next run.
- **Rule 4.C**: Resonance frequencies typically occur at 7,200 RPM. Avoid prolonged operation in the 7,100-7,300 RPM band.

## 5. Maintenance
Rotor inspection must be conducted every 500 operational hours. Lubrication of the main spindle bearing is required bi-annually. Use only BioOps certified synthetic lubricants.
