# CENT-01 Laboratory Centrifuge Calibration and Operation Manual

**Document ID:** MAN-CENT01-CAL-v3.2  
**Revision Date:** 2026-03-15  
**Equipment:** BioOps CENT-01 High-Speed Precision Centrifuge  
**Classification:** GxP Controlled Document  

---

## 1. Introduction

The CENT-01 is a high-speed, precision laboratory centrifuge designed for biological sample separation, cell pelleting, and density gradient fractionation. This manual covers the standard operating procedures, calibration protocols, and safety limits for the CENT-01 model.

All operators must complete GMP Module 7 training before operating this equipment unsupervised. Operations must be logged in the electronic batch record (EBR) system.

## 2. General Operation

To ensure safety and equipment longevity, operators must adhere to strict payload-to-RPM ratios. Excessive RPM on heavy payloads can cause severe resonant vibration, potentially leading to catastrophic hardware failure or sample destruction.

The device supports a maximum theoretical rotational speed of 15,000 RPM under zero-load conditions. The rotor arm radius is 0.15 m (150 mm), which determines the Relative Centrifugal Force (RCF) at any given speed.

### 2.1. RCF Calculation

The Relative Centrifugal Force is calculated using:

```
RCF = 1.118 × 10⁻⁵ × r × RPM²
```

Where `r` is the rotor radius in centimetres (15 cm for CENT-01).

| RPM    | RCF (×g) |
|--------|----------|
| 1,000  | 168 ×g   |
| 3,000  | 1,509 ×g |
| 5,000  | 4,193 ×g |
| 8,000  | 10,733 ×g|
| 10,000 | 16,770 ×g|
| 15,000 | 37,733 ×g|

### 2.2. Startup Sequence

1. Verify rotor is properly seated and locked (torque: 25 N·m).
2. Load samples symmetrically — maximum imbalance tolerance is ±0.5 g.
3. Close lid and verify magnetic interlock engages.
4. Set target RPM via the BioOps Twin control interface.
5. Monitor vibration telemetry during the ramp-up phase.

## 3. Calibration Tables

The following tables outline the maximum safe RPM and expected vibration (RMS g-force) limits based on the payload mass.

### 3.1. Standard Rotor Calibration (Rotor SR-150)

| Payload Mass (g) | Max Safe RPM | Expected RCF (×g) | Warning Vibration Limit (g) | Critical Shutdown Limit (g) |
|------------------|--------------|--------------------|-----------------------------|------------------------------|
| 10g              | 12,000 RPM   | 24,148 ×g          | 0.25 g                      | 0.50 g                      |
| 25g              | 10,000 RPM   | 16,770 ×g          | 0.28 g                      | 0.55 g                      |
| 50g              | 8,000 RPM    | 10,733 ×g          | 0.30 g                      | 0.60 g                      |
| 100g             | 5,000 RPM    | 4,193 ×g           | 0.35 g                      | 0.70 g                      |
| 250g             | 3,000 RPM    | 1,509 ×g           | 0.40 g                      | 0.80 g                      |
| 500g             | 1,500 RPM    | 377 ×g             | 0.50 g                      | 1.00 g                      |

### 3.2. Heavy Duty Rotor Calibration (Rotor HD-250)

| Payload Mass (g) | Max Safe RPM | Expected RCF (×g) | Warning Vibration Limit (g) | Critical Shutdown Limit (g) |
|------------------|--------------|--------------------|-----------------------------|------------------------------|
| 100g             | 7,000 RPM    | 8,217 ×g           | 0.30 g                      | 0.65 g                      |
| 250g             | 4,500 RPM    | 3,396 ×g           | 0.35 g                      | 0.75 g                      |
| 500g             | 2,500 RPM    | 1,048 ×g           | 0.40 g                      | 0.85 g                      |
| 1000g            | 1,000 RPM    | 168 ×g             | 0.55 g                      | 1.10 g                      |

### 3.3. Common Protocols by Sample Type

| Application                      | Recommended RPM | Duration  | Rotor  |
|----------------------------------|-----------------|-----------|--------|
| Blood serum separation           | 3,000 RPM       | 10 min    | SR-150 |
| Cell pelleting (mammalian)       | 1,500 RPM       | 5 min     | SR-150 |
| Bacterial culture harvest        | 5,000 RPM       | 15 min    | SR-150 |
| DNA extraction (ethanol precip.) | 12,000 RPM      | 30 min    | SR-150 |
| Density gradient (sucrose)       | 8,000 RPM       | 60 min    | HD-250 |
| Protein pellet (ammonium sulfate)| 10,000 RPM      | 20 min    | SR-150 |

## 4. Resonance and Vibration Safety

### 4.1. Structural Resonance Zone

The CENT-01 has a documented natural frequency resonance band between **7,000–8,000 RPM**. Operating within this band causes amplified harmonic vibrations due to Lorentzian resonance coupling between the rotor shaft and bearing assembly.

**Mitigation strategies:**
- Ramp through the 7,000–8,000 RPM zone rapidly (do not hold steady-state).
- If target RPM is within the resonance band, consider alternative protocols.
- The BioOps Twin AI agent will automatically warn when approaching this zone.

### 4.2. Vibration Anomaly Detection

The system employs a rolling Z-Score algorithm (window = 20 data points) for statistical anomaly detection:

- **Z < 2.0**: Normal operating vibration.
- **2.0 ≤ Z < 3.0**: Elevated — monitor closely.
- **Z ≥ 3.0**: Statistical anomaly detected — automatic alert generated. AI agent will recommend corrective action.

### 4.3. Vibration Troubleshooting

| Symptom                         | Probable Cause                 | Corrective Action                        |
|---------------------------------|--------------------------------|------------------------------------------|
| Gradual vibration increase      | Bearing wear                   | Schedule maintenance, reduce max RPM     |
| Sudden vibration spike          | Sample imbalance               | Stop, redistribute samples, restart      |
| Vibration only at specific RPM  | Structural resonance           | Avoid steady-state in resonance band     |
| Persistent high vibration       | Rotor misalignment             | Stop immediately, mechanical inspection  |

## 5. Emergency Procedures

If the telemetry system detects a vibration exceeding the Critical Shutdown Limit, the centrifuge will automatically engage the EMERGENCY_STOP protocol.

- **Rule 5.A**: Under no circumstances should an operator attempt to override an EMERGENCY_STOP.
- **Rule 5.B**: After an EMERGENCY_STOP, the centrifuge requires a full mechanical reset and recalibration before the next run. Document the event in the incident report form (IRF-CENT01).
- **Rule 5.C**: Resonance frequencies typically occur at 7,200 RPM. Avoid prolonged operation in the 7,000–8,000 RPM band.
- **Rule 5.D**: If EMERGENCY_STOP triggers more than twice in 24 hours, take the equipment offline and escalate to the Engineering team.

## 6. Preventive Maintenance Schedule

| Task                                 | Frequency            | Responsible      |
|--------------------------------------|----------------------|------------------|
| Visual rotor inspection              | Before each run      | Operator         |
| Bearing lubrication (synthetic)      | Every 500 hours      | Maintenance Tech |
| Full vibration baseline calibration  | Every 1,000 hours    | QC Engineer      |
| Rotor dynamic balancing              | Annually             | OEM Technician   |
| Control system firmware update       | Per manufacturer     | IT/Engineering   |
| Magnetic interlock test              | Monthly              | Safety Officer   |

**Note:** Use only BioOps certified synthetic lubricants (Part No. LUB-SYN-500). Third-party lubricants may void the warranty and compromise vibration characteristics.

## 7. Regulatory Compliance

This equipment and its digital twin system are designed to support compliance with:
- **FDA 21 CFR Part 11** — Electronic records and signatures
- **EU GMP Annex 11** — Computerised systems
- **ISO 17025** — General requirements for the competence of testing and calibration laboratories

All calibration events, AI-recommended parameters, and operator approvals are recorded in an immutable JSONL audit trail.
