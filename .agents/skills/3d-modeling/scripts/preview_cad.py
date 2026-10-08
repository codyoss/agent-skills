#!/usr/bin/env python3
"""Headless CAD export and preview rendering utility.

Compiles OpenSCAD, build123d Python, or headless Blender scripts into STL/STEP models
and generates thumbnail preview PNG images.
"""
import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def die(msg, code=1):
    sys.stdout.flush()
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def find_python_interpreter():
    """Find appropriate Python interpreter with CAD libraries (build123d)."""
    # 1. Custom env override
    if os.environ.get("CAD_PYTHON"):
        return os.environ.get("CAD_PYTHON")
    # 2. Dedicated 3d venv
    venv_py = Path("~/3d/.venv/bin/python").expanduser()
    if venv_py.exists():
        return str(venv_py)
    # 3. Active virtual environment
    if os.environ.get("VIRTUAL_ENV"):
        act_py = Path(os.environ["VIRTUAL_ENV"]) / "bin" / "python"
        if act_py.exists():
            return str(act_py)
    # 4. System Python
    return sys.executable


def run_cmd(cmd, check=True):
    """Run subprocess command and capture output."""
    r = subprocess.run(cmd, capture_output=True, text=True)
    if check and r.returncode != 0:
        print(r.stdout[-2000:], r.stderr[-2000:], sep="\n", file=sys.stderr)
        die(f"Command failed with exit code {r.returncode}: {' '.join(cmd)}")
    return r


def render_stl_preview_openscad(stl_path, png_path):
    """Generate a preview PNG of an STL file using OpenSCAD."""
    if not shutil.which("openscad"):
        return False

    temp_scad = stl_path.with_suffix(".preview.scad")
    try:
        temp_scad.write_text(f'import("{stl_path.name}");\n')
        cmd = [
            "openscad",
            "-o", str(png_path),
            "--imgsize=800,600",
            "--autocenter",
            "--viewall",
            str(temp_scad),
        ]
        r = run_cmd(cmd, check=False)
        if r.returncode != 0 and shutil.which("xvfb-run"):
            run_cmd(["xvfb-run", "-a"] + cmd, check=False)
    finally:
        if temp_scad.exists():
            temp_scad.unlink()
    return png_path.exists()


def process_openscad(in_file, outdir, generate_png=True):
    """Export STL and PNG preview from an OpenSCAD script."""
    if not shutil.which("openscad"):
        die("OpenSCAD is not installed. Install via your system package manager (e.g. pacman -S openscad).")

    out_stl = outdir / f"{in_file.stem}.stl"
    out_png = outdir / f"{in_file.stem}.png"

    print(f"Compiling OpenSCAD model -> {out_stl}...")
    run_cmd(["openscad", "-o", str(out_stl), str(in_file)])
    print(f"✅ Generated: {out_stl}")

    if generate_png:
        print(f"Rendering preview -> {out_png}...")
        cmd = [
            "openscad",
            "-o", str(out_png),
            "--imgsize=800,600",
            "--autocenter",
            "--viewall",
            str(in_file),
        ]
        r = run_cmd(cmd, check=False)
        if r.returncode != 0 and shutil.which("xvfb-run"):
            r = run_cmd(["xvfb-run", "-a"] + cmd, check=False)
        if out_png.exists():
            print(f"✅ Generated: {out_png}")
        else:
            print("Warning: Could not generate preview PNG image.", file=sys.stderr)

    return out_stl, out_png if out_png.exists() else None


def process_build123d(in_file, outdir, generate_png=True):
    """Execute build123d script to export STL/STEP, then generate preview."""
    py_bin = find_python_interpreter()
    out_stl = outdir / f"{in_file.stem}.stl"
    out_png = outdir / f"{in_file.stem}.png"

    print(f"Executing Python CAD script ({py_bin}) -> {in_file}...")
    env = dict(os.environ)
    env["CAD_OUTPUT_STL"] = str(out_stl)
    env["CAD_OUTPUT_DIR"] = str(outdir)

    r = subprocess.run([py_bin, str(in_file), str(out_stl)], env=env, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-2000:], r.stderr[-2000:], sep="\n", file=sys.stderr)
        die(f"Execution failed (exit {r.returncode})")

    # If script did not accept CLI argument, check if it wrote to outdir or stem
    if not out_stl.exists():
        candidates = list(outdir.glob(f"{in_file.stem}*.stl")) + list(in_file.parent.glob(f"{in_file.stem}*.stl"))
        if candidates:
            shutil.move(candidates[0], out_stl)

    if out_stl.exists():
        print(f"✅ Generated: {out_stl}")
    else:
        print(f"Warning: Expected output {out_stl} was not created directly by script.", file=sys.stderr)

    if generate_png and out_stl.exists():
        print(f"Rendering preview -> {out_png}...")
        render_stl_preview_openscad(out_stl, out_png)
        if out_png.exists():
            print(f"✅ Generated: {out_png}")

    return out_stl if out_stl.exists() else None, out_png if out_png.exists() else None


def process_blender(in_file, outdir, generate_png=True):
    """Run Blender headless Python script to export STL and render preview."""
    if not shutil.which("blender"):
        die("Blender is not installed. Install via your system package manager (e.g. pacman -S blender).")

    out_stl = outdir / f"{in_file.stem}.stl"
    out_png = outdir / f"{in_file.stem}.png"

    print(f"Executing Blender headless script -> {in_file}...")
    cmd = [
        "blender",
        "--background",
        "--factory-startup",
        "--python", str(in_file),
        "--",
        str(out_stl),
    ]
    run_cmd(cmd)

    if out_stl.exists():
        print(f"✅ Generated: {out_stl}")
    else:
        die(f"Blender script did not produce {out_stl}")

    if generate_png and out_stl.exists():
        print(f"Rendering preview -> {out_png}...")
        render_stl_preview_openscad(out_stl, out_png)
        if out_png.exists():
            print(f"✅ Generated: {out_png}")

    return out_stl, out_png if out_png.exists() else None


def main():
    p = argparse.ArgumentParser(
        description="Compile CAD files (OpenSCAD, build123d, Blender) and render previews.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("file", help="Input CAD file (.scad or .py)")
    p.add_argument("--outdir", help="Output directory for generated models and previews")
    p.add_argument("--no-png", action="store_true", help="Skip generating thumbnail PNG preview")
    args = p.parse_args()

    in_file = Path(args.file).expanduser().resolve()
    if not in_file.exists():
        die(f"Input file not found: {in_file}")

    outdir = Path(args.outdir).expanduser().resolve() if args.outdir else in_file.parent
    outdir.mkdir(parents=True, exist_ok=True)

    ext = in_file.suffix.lower()
    if ext == ".scad":
        process_openscad(in_file, outdir, generate_png=not args.no_png)
    elif ext == ".py":
        # Check script contents to determine build123d vs blender
        content = in_file.read_text(errors="replace")
        if "import bpy" in content:
            process_blender(in_file, outdir, generate_png=not args.no_png)
        else:
            process_build123d(in_file, outdir, generate_png=not args.no_png)
    else:
        die(f"Unsupported file extension '{ext}'. Expected .scad or .py")


if __name__ == "__main__":
    main()
