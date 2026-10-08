# build123d Guide

`build123d` is a Python-based parametric CAD library built upon OpenCASCADE technology. It brings modern Python syntax to engineering CAD with native support for fillets, chamfers, complex constraint sketches, and standard engineering formats like STEP.

---

## 1. When to Use build123d

- **Best for**: Precision mechanical engineering, parts requiring fillets and edge chamfers, threaded fasteners, multi-body assemblies, and exporting industry-standard STEP files for CNC machining or injection molding.
- **Python Compatibility**: Install in an isolated virtual environment (`python ≤ 3.12` recommended for pre-built wheel compatibility).

---

## 2. Virtual Environment Setup

To avoid system package conflicts:
```bash
python -m venv ~/3d/.venv
~/3d/.venv/bin/pip install --upgrade pip build123d
```

---

## 3. Essential Syntax & Modeling Patterns

### Builder Mode: Box with Hole and Fillet
```python
import os
import sys
from build123d import *

with BuildPart() as p:
    # 1. Base solid
    Box(60, 40, 15)

    # 2. Subtractive hole
    Cylinder(radius=6, height=20, mode=Mode.SUBTRACT)

    # 3. Fillet top edges
    top_edges = p.edges().filter_by(Axis.Z, reverse=True)
    fillet(top_edges, radius=3.0)

# Export to STL and STEP
output_path = sys.argv[1] if len(sys.argv) > 1 else "model.stl"
export_stl(p.part, output_path)
export_step(p.part, os.path.splitext(output_path)[0] + ".step")
print(f"Exported {output_path}")
```

### Algebra Mode (Object-Oriented Operations)
```python
from build123d import Box, Cylinder, Axis, fillet, export_stl

# Combine primitives with algebraic operators (+ and -)
part = Box(50, 50, 20) - Cylinder(radius=8, height=30)
part = fillet(part.edges().group_by(Axis.Z)[-1], radius=2.5)

export_stl(part, "algebra_model.stl")
```

### 2D Sketch Extrusion
```python
from build123d import *

with BuildPart() as p:
    with BuildSketch(Plane.XY) as s:
        Circle(radius=25)
        Rectangle(15, 15, mode=Mode.SUBTRACT)
    extrude(amount=12)

export_stl(p.part, "extruded_part.stl")
```

---

## 4. Headless Execution

Execute via the dedicated virtual environment:
```bash
~/3d/.venv/bin/python model.py out.stl
```
Or using the skill helper script:
```bash
python3 <skill-dir>/scripts/preview_cad.py model.py
```
