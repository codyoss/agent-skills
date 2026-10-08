# Moonraker API Reference

Moonraker provides the HTTP REST and WebSocket control interface for Klipper 3D printers. All interactions in this skill utilize standard HTTP endpoints.

---

## 1. Safe Read-Only Endpoints

Read-only queries can be performed safely via `scripts/printer.py get <path>` without human approval:

| Endpoint | Purpose | Returned Data |
|---|---|---|
| `GET /printer/info` | Printer state | Klipper state (`ready`, `startup`, `shutdown`, `error`), hostname, software version. |
| `GET /server/info` | Server status | Moonraker components, active plugins, warnings. |
| `GET /printer/objects/list` | Introspection | List of all inspectable Klipper object names. |
| `GET /printer/objects/query?print_stats&virtual_sdcard` | Print progress | Active filename, state (`printing`, `paused`, `complete`), progress fraction (0.0..1.0), print duration. |
| `GET /printer/objects/query?extruder&heater_bed` | Temperatures | Current temperature and target setpoints for nozzle and heated bed. |
| `GET /printer/objects/query?temperature_sensor%20chamber_temp` | Chamber temp | Internal build chamber ambient temperature. |
| `GET /printer/objects/query?filament_switch_sensor%20filament_sensor` | Runout sensor | Whether filament is currently loaded into the toolhead. |
| `GET /printer/objects/query?toolhead=axis_minimum,axis_maximum` | Travel limits | Physical motion limits of X, Y, and Z axes. |
| `GET /printer/objects/query?box` | CFS / Material box | Creality Filament System status: connected slots (`T1A`..`T4D`), material type, and color hex. |
| `GET /printer/objects/query?exclude_object` | Object exclusion | Individual part tracking within a multi-part print (useful for canceling failed parts). |
| `GET /printer/objects/query?bed_mesh` | Bed topography | Calibrated bed mesh leveling profile matrix. |
| `GET /server/files/list?root=gcodes` | Stored G-codes | List of files uploaded to the printer with sizes and modification timestamps. |
| `GET /server/files/metadata?filename=<name>` | Slicer metadata | Estimated print time, filament weight, layer count, and embedded thumbnails. |
| `GET /server/history/list?limit=10&order=desc` | Job history | Past completed or canceled print jobs with durations and status. |
| `GET /machine/system_info` | System stats | CPU usage, memory, network interfaces, and host distribution info. |

*Note: Object names containing spaces must be URL-encoded (e.g. `%20`).*

---

## 2. Mutating Endpoints (Requires User Confirmation)

Any action that moves motors, applies heat, or alters job execution must be guarded with explicit user confirmation (`--yes` in CLI commands):

| Action | Endpoint | Method / Payload |
|---|---|---|
| **Upload G-code** | `/server/files/upload` | Multipart POST (`file`, `root=gcodes`, optional `print=true`) |
| **Start Job** | `/printer/print/start` | POST JSON `{"filename": "part.gcode"}` |
| **Pause Job** | `/printer/print/pause` | POST JSON `{}` *(safe immediate action)* |
| **Resume Job** | `/printer/print/resume` | POST JSON `{}` *(requires confirmation)* |
| **Cancel Job** | `/printer/print/cancel` | POST JSON `{}` *(requires confirmation)* |
| **Emergency Stop** | `/printer/emergency_stop` | POST JSON `{}` *(immediate shutdown)* |

---

## 3. Deliberately Restricted Operations

The following endpoints execute unconstrained hardware actions or system reboots and should never be invoked without direct, explicit instructions from the user:
- `POST /printer/gcode/script?script=...`: Raw arbitrary G-code injection (manual moves, motor powering, raw heating).
- `DELETE /server/files/gcodes/<name>`: File deletion from printer storage.
- `POST /printer/firmware_restart`: Firmware micro-controller restart.
- `POST /machine/reboot` or `POST /machine/shutdown`: Operating system restart/shutdown.
- Any direct mutation of `printer.cfg`.
