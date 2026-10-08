# OpenSCAD Guide

OpenSCAD is a declarative, programmatic CAD modeling language based on Constructive Solid Geometry (CSG). It is ideal for functional brackets, enclosures, parametric adapters, and geometrically precise parts.

---

## 1. When to Use OpenSCAD

- **Best for**: Functional parts, geometric shapes, dimensional enclosures, mounting brackets, parametric grids.
- **Not suited for**: Complex organic topology, freeform surfacing, or complex filleting of multi-axis intersections (use `build123d` or Blender for those).

---

## 2. Syntax & Essential Patterns

### CSG Primitives & Boolean Operations
```openscad
$fn = 64; // Set circle/cylinder fragment resolution

// Difference: Subtract cylinders (holes) from a solid base
difference() {
    cube([60, 40, 10], center = true);

    // Mounting holes
    translate([20, 10, 0])
        cylinder(r = 2.5, h = 15, center = true);
    translate([-20, -10, 0])
        cylinder(r = 2.5, h = 15, center = true);
}
```

### 2D Profiles with Linear & Rotational Extrusion
```openscad
// Extrude a rounded 2D hull profile into 3D
linear_extrude(height = 15, convexity = 4) {
    hull() {
        circle(r = 10);
        translate([40, 0, 0]) circle(r = 6);
    }
}
```

### Parametric Design Pattern
Always declare dimensions as top-level variables:
```openscad
wall_thickness = 2.0;
inner_width = 50.0;
inner_depth = 30.0;
inner_height = 25.0;

module enclosure() {
    difference() {
        cube([inner_width + 2*wall_thickness, inner_depth + 2*wall_thickness, inner_height + wall_thickness]);
        translate([wall_thickness, wall_thickness, wall_thickness])
            cube([inner_width, inner_depth, inner_height + 1]);
    }
}
enclosure();
```

---

## 3. Headless Export & Preview Commands

OpenSCAD can be invoked completely headless via CLI:

### STL Generation
```bash
openscad -o model.stl model.scad
```

### Preview PNG Thumbnail
```bash
openscad -o preview.png --imgsize=800,600 --autocenter --viewall model.scad
```

### Headless Display Wrapper (`xvfb-run`)
If running in a remote SSH session or container without an X11/Wayland display server:
```bash
xvfb-run -a openscad -o preview.png --imgsize=800,600 --autocenter --viewall model.scad
```
*(Package requirement: `xorg-server-xvfb` on Arch Linux, `xvfb` on Debian/Ubuntu).*
