---
name: 3d-printer
description: >
  Control 3D printers running Klipper and Moonraker over the local network and slice models with OrcaSlicer.
  Use when the user wants to print a 3D model, check printer status, query temperatures or progress,
  inspect loaded filaments or CFS/material slots, run preflight safety checks on G-code, slice models headlessly,
  upload print jobs, or discover printers on the local network. Don't use for authoring CAD code or 3D modeling.
metadata:
  version: 1.0.0
  author: "Cody Oss"
license: "MIT"
---

# 3D Printer Control & Slicing

This skill provides automated network control for Klipper/Moonraker 3D printers and headless slicing via OrcaSlicer.

All operations run through two bundled Python scripts:
- **`scripts/printer.py`**: Telemetry, preflight safety inspection, OrcaSlicer CLI slicing, file upload, and print job execution.
- **`scripts/find_printer.py`**: Dynamic local network discovery (Moonraker port sweep and ARP resolution) to detect printers and maintain local config without hardcoding machine details.

---

## Safety Protocol: Physical Machine Protection

3D printers heat elements to high temperatures and actuate high-speed stepper motors. Unattended or unauthorized commands can crash nozzles, damage build plates, or cause fire hazards.

1. **Explicit User Consent (`--yes`)**:
   - Commands that start, resume, cancel, or emergency stop (`start`, `resume`, `cancel`, `estop`, and `upload --start`) **refuse to run without `--yes`**.
   - Pass `--yes` **only** after the user has explicitly given confirmation in the current conversation for that exact job.
   - Before requesting confirmation, display the print summary: filename, estimated duration, filament usage (weight and type), and preflight bounding box.
   - Remind the user to verify that the build bed is clear and the correct material is loaded.
2. **Immediate Pause Exception**:
   - `scripts/printer.py pause` is an immediate safe intervention. Call it without waiting for confirmation if a print anomaly or safety issue is observed or requested.
3. **Preflight Guard**:
   - Never upload or start unverified G-code. Always run `check` first to verify that extrusion coordinates fit within physical machine limits.

---

## Command Reference

Set the script path alias:
```bash
PRINTER=<this skill's base directory>/scripts/printer.py
DISCOVER=<this skill's base directory>/scripts/find_printer.py
```

### Telemetry & Monitoring (Read-Only)

| Goal | Command |
|---|---|
| Comprehensive status (state, progress %, temps, ETA, filament) | `python3 $PRINTER status` |
| List files stored on printer (newest first) | `python3 $PRINTER files [--limit 20]` |
| Recent print history | `python3 $PRINTER history [--limit 10]` |
| Query any Moonraker endpoint | `python3 $PRINTER get "/printer/objects/query?box"` |
| Discover/refresh printer on local network | `python3 $DISCOVER` |

*For additional Moonraker endpoints (CFS/AMS multi-material, exclude-object, bed mesh), consult [moonraker_api.md](references/moonraker_api.md).*

### Slicing & Preflight Verification

| Goal | Command |
|---|---|
| Slice STL/3MF/STEP with OrcaSlicer | `python3 $PRINTER slice model.stl [--outdir DIR] [--orient] [--no-arrange]` |
| Preflight check local G-code | `python3 $PRINTER check model.gcode` |

*Note: Slicing automatically executes preflight checks on generated plate G-codes.*

### Job Management (Hardware Execution)

| Goal | Command | Human Confirmation |
|---|---|---|
| Upload G-code to printer | `python3 $PRINTER upload model.gcode` | Not needed (stored only) |
| Upload and start print immediately | `python3 $PRINTER upload model.gcode --start --yes` | **Required (`--yes`)** |
| Start existing file from printer memory | `python3 $PRINTER start "name.gcode" --yes` | **Required (`--yes`)** |
| Pause active print | `python3 $PRINTER pause` | Immediate (safe action) |
| Resume paused print | `python3 $PRINTER resume --yes` | **Required (`--yes`)** |
| Cancel active print | `python3 $PRINTER cancel --yes` | **Required (`--yes`)** |
| Emergency stop (e-stop) | `python3 $PRINTER estop --yes` | **Required (`--yes`)** |

---

## Standard Workflow: Model to Print

1. **Verify File Location**:
   Ensure CAD model files reside under the user's home directory (e.g. `~/3d/projects/<name>/part.stl`). OrcaSlicer Flatpak cannot access `/tmp`.
2. **Slice Model**:
   ```bash
   python3 $PRINTER slice ~/3d/projects/<name>/part.stl
   ```
   This generates `<name>.gcode` in `out/` and runs preflight verification.
3. **Review Preflight Report**:
   Verify time, filament weight, and ensure no `PROBLEM:` alerts are reported. Extrusion bounding boxes must lie strictly within machine travel limits.
4. **Check Printer Availability**:
   ```bash
   python3 $PRINTER status
   ```
   Confirm Klipper state is `ready` and state is `standby` (not currently printing).
5. **Request Human Confirmation & Print**:
   Present the file name, estimated time, and filament requirements to the user. Upon confirmation:
   ```bash
   python3 $PRINTER upload out/part.gcode --start --yes
   ```
6. **Track Progress**:
   Query status periodically. Do not poll in tight loops; intervals of 2–5 minutes are appropriate.

---

## Configuration & Network Setup

Printer settings, network IPs, and hardware limits are stored locally on the host machine to avoid exposing private hardware data:
- Configuration details, JSON schema, and environment variables are documented in [configuration.md](references/configuration.md).
- If the printer IP changes (DHCP renewal) or when migrating to a new machine, run:
  ```bash
  python3 $DISCOVER
  ```
  The discovery tool scans the local subnet for Moonraker, verifies the device via ARP, queries hardware limits, and updates local configuration automatically.

---

## Troubleshooting

- **"Can't reach printer at http://..."**:
  The printer's IP may have changed via DHCP. Run `python3 scripts/find_printer.py` to auto-detect and update the IP.
- **Slicing fails with parameter out of range**:
  OrcaSlicer CLI mode enforces strict range checks on JSON profiles. If a vendor profile parameter exceeds allowable bounds (e.g., `retraction_distances_when_cut`), inspect and adjust the value in `~/3d/profiles/machine.json` as documented in [configuration.md](references/configuration.md).
- **Klipper state is `shutdown` or `error`**:
  Do not attempt to bypass or send raw restart commands. Report the error state to the user so they can inspect the physical machine and clear any faults from the printer display.
