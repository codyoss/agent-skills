#!/usr/bin/env python3
"""Control Klipper/Moonraker 3D printers and slice models with OrcaSlicer.

Stdlib only. Dynamically reads printer settings from local config file
(default ~/3d/printer.json, override with PRINTER_CONFIG or K2_CONFIG).
Commands that move motors or heat elements require --yes confirmation.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CONFIG_PATH = Path(
    os.environ.get("PRINTER_CONFIG")
    or os.environ.get("K2_CONFIG")
    or "~/3d/printer.json"
).expanduser()

PROFILE_DIR = Path(
    os.environ.get("PRINTER_PROFILES")
    or os.environ.get("K2_PROFILES")
    or "~/3d/profiles"
).expanduser()

ACTIVE_STATES = {"printing", "paused"}


def die(msg, code=1):
    sys.stdout.flush()
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def find_orca_cmd():
    """Detect available OrcaSlicer executable or Flatpak command."""
    env_orca = os.environ.get("PRINTER_ORCA") or os.environ.get("K2_ORCA")
    if env_orca:
        return env_orca.split()

    if shutil.which("orca-slicer"):
        return ["orca-slicer"]

    if shutil.which("flatpak"):
        for app_id in ("com.orcaslicer.OrcaSlicer", "io.github.softfever.OrcaSlicer"):
            try:
                r = subprocess.run(["flatpak", "info", app_id], capture_output=True, text=True)
                if r.returncode == 0:
                    return ["flatpak", "run", app_id]
            except Exception:
                pass

    return ["flatpak", "run", "com.orcaslicer.OrcaSlicer"]


def get_base_url():
    """Retrieve base Moonraker URL from env or local config."""
    env_ip = os.environ.get("PRINTER_IP") or os.environ.get("K2_IP")
    env_port = os.environ.get("PRINTER_PORT") or os.environ.get("K2_PORT")

    if env_ip:
        port = int(env_port) if env_port else 7125
        return f"http://{env_ip}:{port}"

    if not CONFIG_PATH.exists():
        die(
            f"Config file {CONFIG_PATH} not found.\n"
            "Run printer discovery first:\n"
            "  python3 <skill-dir>/scripts/find_printer.py\n"
            "Or set PRINTER_IP environment variable."
        )

    try:
        cfg = json.loads(CONFIG_PATH.read_text())
    except Exception as e:
        die(f"Failed to read {CONFIG_PATH}: {e}")

    ip = cfg.get("last_known_ip")
    port = cfg.get("ports", {}).get("moonraker", 7125)
    if not ip:
        die(
            f"No 'last_known_ip' in {CONFIG_PATH}.\n"
            "Run discovery to locate your printer on the network:\n"
            "  python3 <skill-dir>/scripts/find_printer.py"
        )
    return f"http://{ip}:{port}"


def api(method, path, params=None, timeout=10):
    base = get_base_url()
    url = base + path
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode()
    except urllib.error.HTTPError as e:
        die(f"{method} {path} -> HTTP {e.code}: {e.read().decode()[:500]}")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        die(f"Can't reach printer at {base} ({e}). If the printer IP changed, run find_printer.py.")
    return json.loads(body).get("result") if body else None


def query(*objects):
    return api("GET", "/printer/objects/query?" + "&".join(urllib.parse.quote(o, safe="=,") for o in objects))["status"]


def fmt_dur(sec):
    sec = int(sec or 0)
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h}h{m:02d}m" if h else f"{m}m{s:02d}s"


def print_state():
    return query("print_stats")["print_stats"]["state"]


# ---------- read-only ----------

def cmd_status(a):
    objects = [
        "webhooks",
        "print_stats",
        "virtual_sdcard",
        "extruder",
        "heater_bed",
        "display_status",
        "temperature_sensor chamber_temp",
        "filament_switch_sensor filament_sensor",
    ]
    try:
        s = query(*objects)
    except Exception:
        # Fall back to minimal set if sensor names differ
        s = query("webhooks", "print_stats", "virtual_sdcard", "extruder", "heater_bed", "display_status")

    ps = s["print_stats"]
    vs = s.get("virtual_sdcard", {})
    ex = s.get("extruder", {})
    bed = s.get("heater_bed", {})
    chamber = s.get("temperature_sensor chamber_temp", {}).get("temperature")
    runout = s.get("filament_switch_sensor filament_sensor", {})
    progress = vs.get("progress") or s.get("display_status", {}).get("progress") or 0

    out = {
        "klippy": s.get("webhooks", {}).get("state"),
        "state": ps.get("state"),
        "file": ps.get("filename") or None,
        "progress_pct": round(progress * 100, 1),
        "elapsed": fmt_dur(ps.get("print_duration")),
        "layer": f'{ps.get("info", {}).get("current_layer", 0)}/{ps.get("info", {}).get("total_layer", 0)}',
        "nozzle": f'{ex.get("temperature", 0):.0f}/{ex.get("target", 0):.0f}C',
        "bed": f'{bed.get("temperature", 0):.0f}/{bed.get("target", 0):.0f}C',
        "chamber": f"{chamber:.0f}C" if chamber is not None else None,
        "filament_present": runout.get("filament_detected"),
        "message": ps.get("message") or None,
    }
    if ps.get("state") == "printing" and progress > 0.02:
        out["eta_remaining"] = fmt_dur(ps["print_duration"] / progress - ps["print_duration"])
    print(json.dumps(out, indent=2))


def cmd_files(a):
    files = api("GET", "/server/files/list", {"root": "gcodes"})
    files.sort(key=lambda f: f.get("modified", 0), reverse=True)
    for f in files[: a.limit]:
        when = time.strftime("%Y-%m-%d %H:%M", time.localtime(f.get("modified", 0)))
        print(f'{when}  {f.get("size", 0)/1e6:7.1f} MB  {f["path"]}')


def cmd_history(a):
    jobs = api("GET", "/server/history/list", {"limit": a.limit, "order": "desc"})["jobs"]
    for j in jobs:
        when = time.strftime("%Y-%m-%d %H:%M", time.localtime(j.get("start_time", 0)))
        print(f'{when}  {j.get("status", "unknown"):<10} {fmt_dur(j.get("print_duration")):>8}  {j.get("filename")}')


def cmd_get(a):
    if not a.path.startswith("/"):
        die("Path must start with / (e.g. /printer/objects/query?extruder)")
    print(json.dumps(api("GET", a.path), indent=2))


# ---------- G-code checks ----------

def machine_limits():
    """Query live limits from toolhead, or fall back to local config."""
    try:
        th = query("toolhead=axis_minimum,axis_maximum")["toolhead"]
        return tuple(th["axis_minimum"][:3]), tuple(th["axis_maximum"][:3])
    except SystemExit:
        pass
    except Exception:
        pass

    if CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text())
            tl = cfg.get("travel_limits")
            if tl:
                min_lim = (float(tl.get("x_min", 0)), float(tl.get("y_min", 0)), float(tl.get("z_min", 0)))
                max_lim = (float(tl.get("x_max", 250)), float(tl.get("y_max", 250)), float(tl.get("z_max", 250)))
                return min_lim, max_lim
        except Exception:
            pass

    # Generic conservative fallback
    return (-5.0, -5.0, -5.0), (250.0, 250.0, 250.0)


def analyze_gcode(path):
    """Return header summary plus the bounding box of extruding moves."""
    info = {"file": str(path)}
    keys = {
        "printer_model": "printer_model",
        "estimated printing time (normal mode)": "est_time",
        "total filament used [g]": "filament_g",
        "max_z_height": "max_z",
        "filament_type": "filament_type",
        "nozzle_diameter": "nozzle",
    }
    hdr = re.compile(r"^;\s*([^=:]+?)\s*[=:]\s*(.+)$")
    word = re.compile(r"([XYZE])(-?\d*\.?\d+)")
    pos = {"X": 0.0, "Y": 0.0, "Z": 0.0}
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    absolute = True
    with open(path, errors="replace") as fh:
        for line in fh:
            if line.startswith(";"):
                m = hdr.match(line)
                if m and m.group(1) in keys and keys[m.group(1)] not in info:
                    info[keys[m.group(1)]] = m.group(2).strip()
                continue
            cmd = line.split(";", 1)[0].strip()
            if not cmd:
                continue
            op = cmd.split()[0].upper()
            if op == "G90":
                absolute = True
            elif op == "G91":
                absolute = False
            elif op in ("G0", "G1", "G2", "G3"):
                vals = dict((k, float(v)) for k, v in word.findall(cmd.upper()))
                for ax in "XYZ":
                    if ax in vals:
                        pos[ax] = vals[ax] if absolute else pos[ax] + vals[ax]
                if vals.get("E", 0) > 0 and ("X" in vals or "Y" in vals):
                    for i, ax in enumerate("XYZ"):
                        lo[i] = min(lo[i], pos[ax])
                        hi[i] = max(hi[i], pos[ax])
    if lo[0] != float("inf"):
        info["extrude_bbox"] = {"min": [round(v, 1) for v in lo], "max": [round(v, 1) for v in hi]}
    return info


def get_expected_model():
    """Retrieve expected printer model from env, or config if defined."""
    env_model = os.environ.get("PRINTER_MODEL") or os.environ.get("K2_MODEL")
    if env_model:
        return env_model
    if CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text())
            return cfg.get("expected_model") or cfg.get("model")
        except Exception:
            pass
    return None


def preflight(path, allow_model_mismatch=False):
    """Print a summary and return a list of problems (empty = OK)."""
    info = analyze_gcode(path)
    problems = []
    model = info.get("printer_model")
    expected_model = get_expected_model()

    if expected_model and model and model != expected_model:
        msg = f'sliced for "{model}", expected "{expected_model}"'
        (print(f"WARNING: {msg}") if allow_model_mismatch else problems.append(msg))

    if "extrude_bbox" not in info:
        problems.append("no extruding moves found; is this a valid print file?")
    else:
        mn, mx = machine_limits()
        bb = info["extrude_bbox"]
        for i, ax in enumerate("XYZ"):
            if bb["min"][i] < mn[i] or bb["max"][i] > mx[i]:
                problems.append(f"{ax} extrusion {bb['min'][i]}..{bb['max'][i]} outside machine {mn[i]}..{mx[i]}")

    print(json.dumps(info, indent=2))
    for p in problems:
        print(f"PROBLEM: {p}")
    if not problems:
        print("PREFLIGHT OK")
    return problems


def cmd_check(a):
    sys.exit(1 if preflight(Path(a.gcode), a.allow_model_mismatch) else 0)


# ---------- slicing ----------

def cmd_slice(a):
    model = Path(a.model).expanduser().resolve()
    if not model.exists():
        die(f"{model} not found")
    if str(model).startswith("/tmp"):
        die("OrcaSlicer Flatpak cannot access host /tmp; store models under your home directory (e.g. ~/3d/projects/...)")

    prof = Path(a.profiles).expanduser()
    machine = prof / "machine.json"
    process = prof / "process.json"
    filament = Path(a.filament).expanduser() if a.filament else prof / "filament.json"

    for p in (machine, process, filament):
        if not p.exists():
            die(f"profile missing: {p}")

    outdir = Path(a.outdir).expanduser().resolve() if a.outdir else model.parent / "out"
    outdir.mkdir(parents=True, exist_ok=True)
    for old in outdir.glob("plate_*.gcode"):
        old.unlink()

    orca_cmd = find_orca_cmd()
    cmd = orca_cmd + [
        "--slice", "0",
        "--arrange", "1" if a.arrange else "0",
        "--orient", "1" if a.orient else "0",
        "--load-settings", f"{machine};{process}",
        "--load-filaments", str(filament),
        "--outputdir", str(outdir),
        str(model),
    ]
    print("$ " + " ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True)
    plates = sorted(outdir.glob("plate_*.gcode"))
    if r.returncode != 0 or not plates:
        print(r.stdout[-3000:], r.stderr[-3000:], sep="\n")
        die(f"slice failed (exit {r.returncode})")

    results = []
    for i, plate in enumerate(plates):
        suffix = "" if len(plates) == 1 else f"_plate{i + 1}"
        dest = outdir / f"{model.stem}{suffix}.gcode"
        shutil.move(plate, dest)
        print(f"\n== {dest}")
        results.append(preflight(dest))
    sys.exit(1 if any(results) else 0)


# ---------- actions touching hardware ----------

def require_yes(a, what):
    if not a.yes:
        die(f"Refusing to {what} without --yes. Confirm with the user first, then re-run with --yes.", 2)


def require_idle():
    state = print_state()
    if state in ACTIVE_STATES:
        die(f"Printer is {state}; finish or cancel the active job first.")
    return state


def cmd_upload(a):
    path = Path(a.gcode).expanduser()
    if not path.exists():
        die(f"{path} not found")
    if preflight(path, a.allow_model_mismatch):
        die("preflight failed; refusing to upload")
    if a.start:
        require_yes(a, "start a print")
        require_idle()

    base = get_base_url()
    remote = a.name or path.name
    cmd = [
        "curl", "-sS", "--fail-with-body", "--max-time", "600",
        "-F", f"file=@{path};filename={remote}",
        "-F", "root=gcodes",
    ]
    if a.start:
        cmd += ["-F", "print=true"]
    cmd.append(f"{base}/server/files/upload")
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        die(f"upload failed: {r.stdout}{r.stderr}")
    res = json.loads(r.stdout)
    print(f"Uploaded as {res.get('item', {}).get('path')}" + ("; print started" if res.get("print_started") else ""))


def cmd_start(a):
    require_yes(a, "start a print")
    require_idle()
    files = api("GET", "/server/files/list", {"root": "gcodes"})
    names = {f.get("path") for f in files}
    if a.name not in names:
        die(f'"{a.name}" is not on the printer. Use `files` command to see available files.')
    api("POST", "/printer/print/start", {"filename": a.name})
    print(f"Started print: {a.name}")


def cmd_pause(a):
    if print_state() != "printing":
        die("Nothing is currently printing.")
    api("POST", "/printer/print/pause")
    print("Paused print")


def cmd_resume(a):
    require_yes(a, "resume printing")
    if print_state() != "paused":
        die("Printer is not paused.")
    api("POST", "/printer/print/resume")
    print("Resumed print")


def cmd_cancel(a):
    require_yes(a, "cancel the print")
    if print_state() not in ACTIVE_STATES:
        die("No active print to cancel.")
    api("POST", "/printer/print/cancel")
    print("Cancelled print")


def cmd_estop(a):
    require_yes(a, "emergency stop")
    api("POST", "/printer/emergency_stop")
    print("EMERGENCY STOP sent. Printer requires a firmware/screen restart before reuse.")


def cmd_discover(a):
    """Delegate to find_printer.py."""
    discovery_script = Path(__file__).parent / "find_printer.py"
    cmd = [sys.executable, str(discovery_script), "--config", str(CONFIG_PATH)]
    if a.force:
        cmd.append("--force")
    if a.subnet:
        cmd += ["--subnet", a.subnet]
    if a.mac:
        cmd += ["--mac", a.mac]
    if a.host:
        cmd += ["--host", a.host]
    if a.dry_run:
        cmd.append("--dry-run")
    subprocess.run(cmd)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="state, progress, temperatures, filament").set_defaults(fn=cmd_status)

    s = sub.add_parser("files", help="G-code files on printer, newest first")
    s.add_argument("--limit", type=int, default=20)
    s.set_defaults(fn=cmd_files)

    s = sub.add_parser("history", help="recent print jobs")
    s.add_argument("--limit", type=int, default=10)
    s.set_defaults(fn=cmd_history)

    s = sub.add_parser("get", help="read-only GET of any Moonraker endpoint")
    s.add_argument("path")
    s.set_defaults(fn=cmd_get)

    s = sub.add_parser("discover", help="scan local network to find printer and update config")
    s.add_argument("--subnet", help="subnet to scan")
    s.add_argument("--mac", help="target MAC address")
    s.add_argument("--host", help="target hostname")
    s.add_argument("--force", action="store_true", help="force full scan")
    s.add_argument("--dry-run", action="store_true")
    s.set_defaults(fn=cmd_discover)

    s = sub.add_parser("check", help="preflight check on a local G-code file")
    s.add_argument("gcode")
    s.add_argument("--allow-model-mismatch", action="store_true")
    s.set_defaults(fn=cmd_check)

    s = sub.add_parser("slice", help="slice model with OrcaSlicer")
    s.add_argument("model")
    s.add_argument("--outdir")
    s.add_argument("--profiles", default=str(PROFILE_DIR))
    s.add_argument("--filament", help="alternate filament .json")
    s.add_argument("--arrange", action=argparse.BooleanOptionalAction, default=True)
    s.add_argument("--orient", action=argparse.BooleanOptionalAction, default=False)
    s.set_defaults(fn=cmd_slice)

    s = sub.add_parser("upload", help="preflight and upload G-code (optionally start)")
    s.add_argument("gcode")
    s.add_argument("--name", help="filename on printer")
    s.add_argument("--start", action="store_true")
    s.add_argument("--yes", action="store_true")
    s.add_argument("--allow-model-mismatch", action="store_true")
    s.set_defaults(fn=cmd_upload)

    s = sub.add_parser("start", help="start an existing G-code file on printer")
    s.add_argument("name")
    s.add_argument("--yes", action="store_true")
    s.set_defaults(fn=cmd_start)

    sub.add_parser("pause", help="pause current print").set_defaults(fn=cmd_pause)

    for name, fn in (("resume", cmd_resume), ("cancel", cmd_cancel), ("estop", cmd_estop)):
        s = sub.add_parser(name)
        s.add_argument("--yes", action="store_true")
        s.set_defaults(fn=fn)

    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
