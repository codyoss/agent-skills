---
name: 3d-modeling
description: >
  Design, generate, inspect, and preview 3D CAD models from code.
  Use when the user wants to model 3D parts using OpenSCAD (.scad), build123d Python (.py),
  or headless Blender scripting, render 2D thumbnail preview images, or export STL and STEP files.
  Don't use for 3D printer hardware control or slicer operations.
metadata:
  version: 1.0.0
  author: "Cody Oss"
license: "MIT"
---

# 3D CAD Modeling from Code

This skill provides workflows for generating 3D models programmatically using OpenSCAD, build123d (Python CAD), and headless Blender scripts, and rendering preview images.

---

## Tool Selection Matrix

Choose the right CAD modeling tool based on design requirements:

| Tool | Primary Use Case | Output Formats | Reference |
|---|---|---|---|
| **OpenSCAD** | Dimensional brackets, geometric solids, enclosures, 2D extruded profiles | `.stl`, `.png` | [openscad_guide.md](references/openscad_guide.md) |
| **build123d** | Precision mechanical parts, fillets, chamfers, threads, multi-body assemblies | `.stl`, `.step` | [build123d_guide.md](references/build123d_guide.md) |
| **Blender** | Organic shapes, artistic sculptures, procedural topology, mesh cleanup | `.stl`, `.obj`, `.blend` | [blender_headless.md](references/blender_headless.md) |

---

## Modeling Workflow

1. **Project Directory**:
   Store modeling source files in project folders under `$HOME` (e.g. `~/3d/projects/<name>/`), which ensures compatibility with sandboxed tools like Flatpak slicers.
2. **Author Code**:
   - For simple dimensional parts: Write `.scad` code using parametric variables for dimensions.
   - For mechanical engineering with fillets: Write Python scripts using `build123d` (executed in `~/3d/.venv/`).
   - For organic geometry: Write headless Python scripts using Blender's `bpy` API.
3. **Compile & Preview**:
   Use the bundled utility `scripts/preview_cad.py` to compile the model to STL and generate a 2D PNG preview thumbnail in one step:
   ```bash
   python3 <this skill's base directory>/scripts/preview_cad.py model.scad --outdir out/
   ```
4. **Inspect the Result**:
   Verify dimensions, wall thicknesses, and check the rendered PNG preview before proceeding to slicing or printing.

---

## Preview & Export Utility

The script `scripts/preview_cad.py` automatically detects the source language and compiles it headlessly:

```bash
CAD_PREVIEW=<this skill's base directory>/scripts/preview_cad.py

# OpenSCAD file -> model.stl + model.png
python3 $CAD_PREVIEW bracket.scad --outdir out/

# build123d script -> part.stl + part.png
python3 $CAD_PREVIEW gear.py --outdir out/

# Blender script -> organic.stl + organic.png
python3 $CAD_PREVIEW sculpture.py --outdir out/
```

- If running headlessly without an active display server (Wayland/X11), the script automatically utilizes `xvfb-run` to render OpenGL previews.

---

## Detailed References

- **OpenSCAD**: Syntax, CSG difference/union patterns, 2D extrusions, and command-line snapshot options are in [openscad_guide.md](references/openscad_guide.md).
- **build123d**: Setup of the isolated Python virtualenv (`~/3d/.venv`), `BuildPart` workflows, edge fillets, and STEP export examples are in [build123d_guide.md](references/build123d_guide.md).
- **Blender Headless**: Scene cleanup, procedural mesh primitives, modifier application, version-compatible STL exports, and camera snapshot rendering are in [blender_headless.md](references/blender_headless.md).
