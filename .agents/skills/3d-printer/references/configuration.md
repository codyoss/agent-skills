# 3D Printer Configuration & Machine Portability

To prevent leaking sensitive network hardware information (such as hardware MAC addresses, private subnet layouts, and static IP addresses) to public repositories, printer connection settings and hardware specifications are stored locally outside of version control.

---

## 1. Local Configuration File

The default configuration file location is:
```text
~/3d/printer.json
```
You can override this location by setting the environment variable:
```bash
export PRINTER_CONFIG="/path/to/your/printer.json"
```

### Schema & Example Template

Below is a clean template for `printer.json` with placeholder values:

```json
{
  "hostname": "my-printer-host",
  "mac_address": "xx:xx:xx:xx:xx:xx",
  "last_known_ip": "192.168.1.50",
  "ports": {
    "moonraker": 7125,
    "web_ui": 4408,
    "creality_ws": 9999
  },
  "nozzle_diameter": 0.4,
  "build_volume": {
    "x": 250,
    "y": 250,
    "z": 250
  },
  "travel_limits": {
    "x_min": -7.0,
    "y_min": -3.0,
    "z_min": -10.0,
    "x_max": 262.0,
    "y_max": 262.0,
    "z_max": 270.0
  },
  "expected_model": "Creality K2"
}
```

### Fields Description

| Field | Description |
|---|---|
| `hostname` | Network hostname returned by Moonraker `/printer/info`. |
| `mac_address` | Hardware MAC address used to re-identify the printer across DHCP IP changes. |
| `last_known_ip` | Last verified IP address on the local network. |
| `ports.moonraker` | Klipper Moonraker HTTP REST port (default: `7125`). |
| `ports.web_ui` | Web interface port (e.g. Fluidd: `4408` or Mainsail: `4409`, or `80`). |
| `build_volume` | Usable printable volume dimensions in millimeters (`x`, `y`, `z`). |
| `travel_limits` | Physical motion limits of the toolhead (`x_min`..`x_max`, etc.). |
| `expected_model` | Optional model name validated against G-code headers during preflight. |

---

## 2. Dynamic Network Auto-Discovery

When deploying this skill on a new workstation, or when a DHCP server assigns a new IP address to the printer, run the automated network discovery script:

```bash
python3 <skill-dir>/scripts/find_printer.py
```

### Discovery Capabilities:
1. **Quick Check**: Checks if the existing `last_known_ip` is online and responsive.
2. **Subnet Scan**: Concurrently probes port 7125 across the local subnet (`/24`) without flooding the network.
3. **Hardware Matching**: Verifies the response against Moonraker `/printer/info` and resolves the device's MAC address from the local ARP cache (`ip neigh`).
4. **Target Matching**: Supports `--mac <MAC>` or `--host <HOSTNAME>` to match a specific device if multiple printers exist on the subnet.
5. **Config Update**: Automatically writes or refreshes the verified IP, MAC, hostname, and travel limits into `~/3d/printer.json`.

---

## 3. Environment Variable Overrides

For headless environments, containerized setups, or quick testing, the following environment variables can override configuration values:

| Variable | Description |
|---|---|
| `PRINTER_CONFIG` | Absolute path to custom `printer.json` file. |
| `PRINTER_IP` | Direct IP override (bypasses config file lookup). |
| `PRINTER_PORT` | Moonraker port override (default: `7125`). |
| `PRINTER_MODEL` | Sliced model name required during preflight (e.g., `Creality K2`). |
| `PRINTER_PROFILES` | Directory containing OrcaSlicer standalone profiles (default: `~/3d/profiles`). |
| `PRINTER_ORCA` | Custom OrcaSlicer executable or Flatpak command string. |

*(Note: Legacy `K2_*` environment variables are also recognized as fallbacks).*

---

## 4. OrcaSlicer Standalone Profiles

OrcaSlicer CLI mode requires standalone resolved JSON files rather than inherited GUI presets:
- `machine.json`: Contains printer geometry, nozzle limits, and start/end G-code macros.
- `process.json`: Layer height, speeds, infill density, and support settings.
- `filament.json`: Temperature, cooling, and extrusion multiplier settings.

### Upstream Range Validation Note
Some stock manufacturer profiles exported from GUI slicers contain values outside the CLI's strict range validation. For example, in certain Creality K2 profiles, `retraction_distances_when_cut` is set to `30`, which fails CLI validation (maximum allowable is `18`). Adjusting this value in `machine.json` resolves the CLI range error.
