# Headless Blender Scripting Guide

Blender includes a complete Python environment (`bpy`) capable of generating, modifying, and exporting complex 3D meshes without launching the graphical user interface.

---

## 1. When to Use Blender

- **Best for**: Organic, artistic, sculpted, procedural, or low-poly geometry; applying advanced modifiers (Subdivision Surface, Remesh, Bevel, Displace); repairing non-manifold meshes; or converting proprietary 3D formats.
- **Not suited for**: High-tolerance dimensional engineering requiring exact parametric dimension constraints (use `build123d` or OpenSCAD).

---

## 2. CLI Execution Pattern

Blender runs headless using the `--background` and `--python` flags. Pass custom arguments to the Python script following the `--` separator:

```bash
blender --background --factory-startup --python script.py -- [output_path]
```

- `--background` (`-b`): Run without a GUI or windowing context.
- `--factory-startup`: Ignore user preferences, add-ons, or custom default `.blend` files for hermetic execution.

---

## 3. Headless Python Script Structure

Below is a robust template for a standalone headless Blender script:

```python
import sys
import bpy

# 1. Clear default scene (default cube, camera, lights)
bpy.ops.wm.read_factory_settings(use_empty=True)

# 2. Procedural Mesh Generation
# Example: Create an icosphere with subdivision
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=15.0, location=(0, 0, 0))
obj = bpy.context.active_object
obj.name = "ArtisticPart"

# 3. Apply Modifiers
subsurf = obj.modifiers.new(name="Subsurf", type="SUBSURF")
subsurf.levels = 2
subsurf.render_levels = 2
bpy.ops.object.modifier_apply(modifier="Subsurf")

# 4. Parse output argument
argv = sys.argv
if "--" in argv:
    output_path = argv[argv.index("--") + 1]
else:
    output_path = "output.stl"

# 5. Export STL (API differs across Blender versions)
if hasattr(bpy.ops.wm, "stl_export"):
    # Blender 4.2+ native operator
    bpy.ops.wm.stl_export(filepath=output_path)
else:
    # Blender <= 4.1 operator
    bpy.ops.export_mesh.stl(filepath=output_path)

print(f"Exported mesh successfully to {output_path}")
```

---

## 4. Headless Rendering of PNG Snapshots

To generate a camera render of the generated mesh directly inside Blender:

```python
import bpy

# Add Camera & Light
scene = bpy.context.scene
cam_data = bpy.data.cameras.new("Camera")
cam_obj = bpy.data.objects.new("Camera", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj
cam_obj.location = (40, -40, 30)
cam_obj.rotation_euler = (1.1, 0, 0.785)

light_data = bpy.data.lights.new(name="Light", type="SUN")
light_obj = bpy.data.objects.new(name="Light", light_data)
scene.collection.objects.link(light_obj)

# Render settings
scene.render.resolution_x = 800
scene.render.resolution_y = 600
scene.render.filepath = "preview.png"
bpy.ops.render.render(write_still=True)
```
