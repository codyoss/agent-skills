#!/usr/bin/env python3
"""Auto-discover Klipper/Moonraker 3D printers on the local network.

Discovers printers dynamically via Moonraker API (port 7125) and ARP table lookup.
Zero hardcoded MACs, IPs, or machine names. Updates the local config file on discovery.
"""
import argparse
import concurrent.futures
import json
import os
import re
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path


def get_default_subnet():
    """Detect local subnet prefix (e.g. '192.168.1') using default route."""
    try:
        out = subprocess.check_output(["ip", "route", "get", "1.1.1.1"], text=True)
        m = re.search(r"src (\d+\.\d+\.\d+)\.\d+", out)
        if m:
            return m.group(1)
    except Exception:
        pass
    return None


def get_mac_for_ip(ip):
    """Retrieve MAC address from local ARP table using 'ip neigh' or /proc/net/arp."""
    try:
        out = subprocess.check_output(["ip", "neigh", "show", ip], text=True)
        m = re.search(r"lladdr ([0-9a-fA-F:]{17})", out)
        if m:
            return m.group(1).lower()
    except Exception:
        pass

    try:
        arp_path = Path("/proc/net/arp")
        if arp_path.exists():
            for line in arp_path.read_text().splitlines()[1:]:
                parts = line.split()
                if len(parts) >= 4 and parts[0] == ip:
                    mac = parts[3].lower()
                    if mac != "00:00:00:00:00:00":
                        return mac
    except Exception:
        pass
    return None


def probe_moonraker(ip, port=7125, timeout=0.8):
    """Check if port is open and returns valid Moonraker info."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        if s.connect_ex((ip, port)) != 0:
            return None
    except Exception:
        return None
    finally:
        s.close()

    url = f"http://{ip}:{port}/printer/info"
    req = urllib.request.Request(url, headers={"User-Agent": "printer-discovery/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout + 0.5) as resp:
            data = json.loads(resp.read().decode())
            return data.get("result", {})
    except Exception:
        return None


def query_toolhead_limits(ip, port=7125, timeout=2.0):
    """Query toolhead axis limits if Moonraker is online."""
    url = f"http://{ip}:{port}/printer/objects/query?toolhead=axis_minimum,axis_maximum"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "printer-discovery/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
            th = data.get("result", {}).get("status", {}).get("toolhead", {})
            return th.get("axis_minimum"), th.get("axis_maximum")
    except Exception:
        return None, None


def main():
    parser = argparse.ArgumentParser(
        description="Discover Klipper/Moonraker 3D printers on the local network.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    default_cfg = os.environ.get("PRINTER_CONFIG") or os.environ.get("K2_CONFIG") or "~/3d/printer.json"
    parser.add_argument("--config", default=default_cfg, help=f"Path to local config file (default: {default_cfg})")
    parser.add_argument("--mac", help="Target MAC address (e.g. aa:bb:cc:dd:ee:ff)")
    parser.add_argument("--host", help="Target hostname to match (e.g. my-klipper-printer)")
    parser.add_argument("--subnet", help="Subnet prefix to scan (e.g. 192.168.1)")
    parser.add_argument("--port", type=int, default=7125, help="Moonraker port (default: 7125)")
    parser.add_argument("--force", action="store_true", help="Force full subnet scan even if current IP is responsive")
    parser.add_argument("--dry-run", action="store_true", help="Print results without saving to config")
    args = parser.parse_args()

    config_path = Path(args.config).expanduser()
    existing_cfg = {}
    if config_path.exists():
        try:
            existing_cfg = json.loads(config_path.read_text())
        except Exception as e:
            print(f"Warning: Failed to parse existing config {config_path}: {e}", file=sys.stderr)

    target_mac = (args.mac or os.environ.get("PRINTER_MAC") or existing_cfg.get("mac_address", "")).lower()
    target_host = args.host or os.environ.get("PRINTER_HOST") or existing_cfg.get("hostname", "")

    # Quick check existing last_known_ip if not forced
    last_ip = os.environ.get("PRINTER_IP") or existing_cfg.get("last_known_ip")
    if last_ip and not args.force:
        print(f"Checking existing IP {last_ip}:{args.port}...")
        info = probe_moonraker(last_ip, args.port, timeout=1.0)
        if info:
            hname = info.get("hostname", "unknown")
            state = info.get("state", "unknown")
            cur_mac = get_mac_for_ip(last_ip) or existing_cfg.get("mac_address", "")
            matches_mac = not target_mac or (cur_mac and cur_mac.lower() == target_mac)
            matches_host = not target_host or (hname and hname.lower() == target_host.lower())

            if matches_mac and matches_host:
                print(f"✅ Printer is reachable at {last_ip} (hostname={hname}, state={state}, mac={cur_mac or 'unresolved'})")
                if not args.dry_run and config_path.exists():
                    updated = False
                    if cur_mac and existing_cfg.get("mac_address") != cur_mac:
                        existing_cfg["mac_address"] = cur_mac
                        updated = True
                    if hname and existing_cfg.get("hostname") != hname:
                        existing_cfg["hostname"] = hname
                        updated = True
                    if updated:
                        config_path.write_text(json.dumps(existing_cfg, indent=2) + "\n")
                        print(f"Updated {config_path} with latest host/mac details.")
                return 0
            print(f"Host at {last_ip} did not match target (mac={cur_mac}, host={hname}). Scanning subnet...")
        else:
            print(f"Printer not responding at {last_ip}. Scanning subnet...")

    # Determine subnet
    subnet = args.subnet
    if not subnet:
        subnet = get_default_subnet()
    if not subnet:
        print("Error: Could not automatically detect local subnet. Specify with --subnet (e.g. --subnet 192.168.1)", file=sys.stderr)
        return 1

    # Clean subnet prefix if user passed CIDR
    if "/" in subnet:
        subnet = subnet.split("/")[0]
    parts = subnet.split(".")
    if len(parts) >= 3:
        subnet = ".".join(parts[:3])

    print(f"Scanning subnet {subnet}.1-254 on port {args.port}...")
    found_printers = []

    def check_candidate(candidate_ip):
        res = probe_moonraker(candidate_ip, args.port, timeout=0.8)
        if res is not None:
            mac = get_mac_for_ip(candidate_ip) or ""
            return {
                "ip": candidate_ip,
                "info": res,
                "mac": mac.lower(),
                "hostname": res.get("hostname", "unknown"),
                "state": res.get("state", "unknown"),
            }
        return None

    ips = [f"{subnet}.{i}" for i in range(1, 255)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        for item in executor.map(check_candidate, ips):
            if item:
                found_printers.append(item)

    if not found_printers:
        print(f"❌ No Moonraker printers detected on subnet {subnet}.0/24 (port {args.port}).", file=sys.stderr)
        return 1

    # Filter by target MAC or hostname if provided
    selected = None
    if target_mac or target_host:
        for p in found_printers:
            mac_match = not target_mac or (p["mac"] and p["mac"] == target_mac)
            host_match = not target_host or (p["hostname"].lower() == target_host.lower())
            if mac_match and host_match:
                selected = p
                break

    if not selected:
        if len(found_printers) == 1:
            selected = found_printers[0]
        else:
            print(f"Found {len(found_printers)} printers on the network:")
            for idx, p in enumerate(found_printers):
                print(f"  [{idx + 1}] IP: {p['ip']:<15} Host: {p['hostname']:<15} MAC: {p['mac'] or 'unknown':<17} State: {p['state']}")
            print("Please specify --mac or --host to pick a specific printer.")
            return 1

    ip = selected["ip"]
    hname = selected["hostname"]
    mac = selected["mac"]
    state = selected["state"]
    print(f"✅ Found printer: IP={ip}, Hostname={hname}, MAC={mac or 'unresolved'}, State={state}")

    # Query limits
    mn, mx = query_toolhead_limits(ip, args.port)
    travel_limits = None
    build_volume = None
    if mn and mx:
        travel_limits = {
            "x_min": mn[0],
            "y_min": mn[1],
            "z_min": mn[2],
            "x_max": mx[0],
            "y_max": mx[1],
            "z_max": mx[2],
        }
        build_volume = {
            "x": round(mx[0] - max(0, mn[0])),
            "y": round(mx[1] - max(0, mn[1])),
            "z": round(mx[2] - max(0, mn[2])),
        }

    # Prepare configuration
    new_cfg = dict(existing_cfg)
    new_cfg["hostname"] = hname
    if mac:
        new_cfg["mac_address"] = mac
    new_cfg["last_known_ip"] = ip
    new_cfg.setdefault("ports", {})["moonraker"] = args.port
    if "web_ui" not in new_cfg.get("ports", {}):
        new_cfg["ports"]["web_ui"] = 4408
    if travel_limits:
        new_cfg["travel_limits"] = travel_limits
    if build_volume:
        new_cfg["build_volume"] = build_volume

    if args.dry_run:
        print("[Dry Run] Would update config with:")
        print(json.dumps(new_cfg, indent=2))
    else:
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(json.dumps(new_cfg, indent=2) + "\n")
        print(f"💾 Updated config: {config_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
