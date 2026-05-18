# CENT-01 Preventive Maintenance and Troubleshooting Guide

**Document ID:** MAN-CENT01-MAINT-v2.1  
**Revision Date:** 2026-02-28  
**Equipment:** BioOps CENT-01 High-Speed Precision Centrifuge  
**Classification:** GxP Controlled Document  

---

## 1. Scope

This document covers the preventive maintenance (PM) program, common failure modes, and troubleshooting procedures for the CENT-01 laboratory centrifuge. It complements the Calibration and Operation Manual (MAN-CENT01-CAL-v3.2).

## 2. Preventive Maintenance Program

### 2.1. Daily Checks (Operator Responsibility)

Before each operational session:

1. **Visual inspection**: Check rotor for visible cracks, corrosion, or debris.
2. **Lid interlock test**: Open and close the lid, verify the magnetic interlock clicks.
3. **Sample balance**: Ensure all tubes are balanced within ±0.5 g across opposing positions.
4. **Drainage check**: Verify the condensation drain is clear and unobstructed.
5. **Software check**: Confirm the BioOps Twin dashboard shows "STANDBY" state and all telemetry values read zero.

### 2.2. Weekly Maintenance (Laboratory Technician)

| Task | Procedure | Acceptance Criteria |
|------|-----------|---------------------|
| Clean rotor chamber | Wipe interior with 70% IPA | No residue visible |
| Check O-ring seals | Inspect door and rotor base seals | No cracking or deformation |
| Test emergency stop button | Press E-STOP, verify rotor decelerates | Full stop within 30 seconds |
| Verify telemetry accuracy | Compare digital readout vs. tachometer | Within ±2% of reference |

### 2.3. Monthly Maintenance (Maintenance Technician)

| Task | Procedure | Acceptance Criteria |
|------|-----------|---------------------|
| Bearing noise assessment | Listen for grinding/clicking at low RPM | Smooth, quiet operation |
| Drive belt tension check | Measure belt deflection (spec: 8–12 mm) | Within manufacturer tolerance |
| Temperature sensor calibration | Compare vs. NIST-traceable thermometer | Within ±0.5°C |
| MQTT telemetry validation | Verify data reaches edge broker | All fields present, latency < 500ms |

### 2.4. Semi-Annual Maintenance (QC Engineer)

| Task | Procedure | Acceptance Criteria |
|------|-----------|---------------------|
| Full vibration baseline | Run at 3000, 5000, 8000, 12000 RPM | Vibration within calibration table limits |
| Bearing lubrication | Apply BioOps LUB-SYN-500 to main spindle | Smooth rotation at hand-turn |
| Rotor balance verification | Dynamic balancing on test stand | Imbalance < 0.1 g·cm |
| Electrical safety test (PAT) | Insulation resistance and earth continuity | Per IEC 61010-1 |

### 2.5. Annual Maintenance (OEM Certified Technician)

| Task | Procedure | Acceptance Criteria |
|------|-----------|---------------------|
| Complete rotor replacement assessment | Inspect rotor fatigue indicators | Pass/fail per OEM criteria |
| Motor brush inspection | Check carbon brush wear depth | Minimum 5 mm remaining |
| Full system recalibration | Run complete calibration protocol | All values within MAN-CENT01-CAL tolerances |
| Firmware update | Apply latest OEM firmware | Successful boot and self-test |

## 3. Common Failure Modes and Root Cause Analysis

### 3.1. Failure Mode: Excessive Vibration During Normal Operation

**Symptoms:** Vibration exceeds warning threshold (>0.25 g) at RPMs previously within spec.

**Root Cause Investigation:**
1. **Sample imbalance** (most common, ~60% of cases): Uneven tube loading or liquid redistribution during spin.
2. **Bearing degradation** (~25%): Lubrication breakdown or particulate contamination.
3. **Rotor fatigue** (~10%): Micro-cracks in rotor body not visible to naked eye.
4. **Environmental** (~5%): Unlevel installation surface, external vibration sources.

**Corrective Actions:**
- Re-balance samples and retry.
- If persistent after re-balancing, schedule bearing inspection.
- If vibration increases progressively over weeks, order rotor NDT (non-destructive testing).

### 3.2. Failure Mode: EMERGENCY_STOP Triggered Unexpectedly

**Symptoms:** System transitions to EMERGENCY_STOP without approaching critical vibration limits.

**Root Cause Investigation:**
1. **Sensor malfunction**: Vibration sensor producing erratic readings.
2. **Z-Score false positive**: Sudden but harmless vibration transient (e.g., building construction nearby).
3. **Electrical noise**: EMI from nearby equipment affecting sensor signal.

**Corrective Actions:**
- Review audit log for the exact vibration and Z-Score values at time of trigger.
- If Z-Score was borderline (3.0–3.5), check for external vibration sources.
- If sensor readings are erratic at standby (non-zero vibration at 0 RPM), recalibrate or replace the accelerometer.

### 3.3. Failure Mode: Rotor Fails to Reach Target RPM

**Symptoms:** Current RPM plateaus below target RPM and does not increase further.

**Root Cause Investigation:**
1. **Drive belt slippage**: Belt too loose or worn.
2. **Motor overload protection**: Excessive payload weight triggering thermal cutout.
3. **Power supply issue**: Insufficient voltage under load.

**Corrective Actions:**
- Check belt tension (spec: 8–12 mm deflection).
- Verify payload weight is within rotor limits.
- Check incoming power supply voltage (spec: 220V ±10%).

## 4. Spare Parts Reference

| Part Number    | Description                   | Recommended Stock |
|----------------|-------------------------------|-------------------|
| ROT-SR150-A    | Standard Rotor SR-150         | 1 unit            |
| ROT-HD250-A    | Heavy Duty Rotor HD-250      | 1 unit            |
| BRG-MAIN-01    | Main spindle bearing assembly | 2 units           |
| BLT-DRV-01     | Drive belt (reinforced)       | 3 units           |
| LUB-SYN-500    | Synthetic lubricant (500 mL)  | 2 bottles         |
| SEN-VIB-01     | Vibration sensor (MEMS)       | 1 unit            |
| SEN-TEMP-01    | Temperature sensor (PT100)    | 1 unit            |
| SEAL-DOOR-01   | Door O-ring seal              | 5 units           |
| SEAL-ROT-01    | Rotor base seal               | 5 units           |
| BRH-CARB-01    | Motor carbon brushes (pair)   | 2 pairs           |

## 5. Decommissioning Procedure

When a CENT-01 unit reaches end-of-life:

1. Run final calibration and archive results.
2. Export complete audit trail from BioOps Twin (JSONL format).
3. Remove and properly dispose of rotor (follow local biohazard waste regulations).
4. Disconnect MQTT telemetry feed and deregister device from edge network.
5. Complete decommissioning form (DCM-CENT01) and file with Quality Assurance.

## 6. Document Control

| Version | Date       | Author            | Changes                         |
|---------|------------|-------------------|---------------------------------|
| v1.0    | 2025-06-15 | Engineering Team  | Initial release                 |
| v2.0    | 2025-11-20 | QC Department     | Added Z-Score troubleshooting   |
| v2.1    | 2026-02-28 | BioOps AI Team    | Added MQTT validation, spare parts |
