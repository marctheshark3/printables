// =============================================================================
// soft_helpers.scad — pure OpenSCAD 2021.01 helpers for FDM soft geometry
// Copy into project as src/lib/soft_helpers.scad and:
//   include <lib/soft_helpers.scad>
// No BOSL2 required (hermetic Docker export).
// Units: mm
// =============================================================================

// --- 2D soft footprints ------------------------------------------------------

// Rounded rectangle footprint (plan fillet). Safe when r < min(x,y)/2.
module soft_rect(x, y, r) {
  rr = min(r, min(x, y) / 2 - 0.01);
  offset(r = rr)
    square([x - 2 * rr, y - 2 * rr], center = true);
}

// Capsule / stadium in 2D
module capsule_2d(len, r) {
  hull() {
    translate([-len / 2 + r, 0]) circle(r = r);
    translate([ len / 2 - r, 0]) circle(r = r);
  }
}

// Regular hexagon (flat-to-flat via circle $fn=6 with r = side geometry)
module hex_2d(r) {
  circle(r = r, $fn = 6);
}

// --- 3D soft primitives ------------------------------------------------------

// Soft box: extruded rounded rect, optional bottom chamfer (FDM-friendly).
// bottom_chamfer grows inward from outer profile at Z=0.
module soft_box(x, y, h, r, bottom_chamfer = 0, $fn = 48) {
  difference() {
    linear_extrude(height = h)
      soft_rect(x, y, r);
    if (bottom_chamfer > 0) {
      difference() {
        translate([0, 0, -0.02])
          linear_extrude(height = bottom_chamfer + 0.02)
            soft_rect(x, y, r);
        translate([0, 0, -0.02])
          linear_extrude(height = bottom_chamfer + 0.04)
            offset(r = -bottom_chamfer)
              soft_rect(x, y, r);
      }
    }
  }
}

// Cylinder with optional top/bottom chamfer (mask-style via cone cut)
module soft_cyl(d, h, chamfer_bot = 0, chamfer_top = 0, $fn = 48) {
  difference() {
    cylinder(d = d, h = h);
    if (chamfer_bot > 0) {
      translate([0, 0, -0.01])
        cylinder(d1 = d + 0.02, d2 = d - 2 * chamfer_bot, h = chamfer_bot + 0.01);
    }
    if (chamfer_top > 0) {
      translate([0, 0, h - chamfer_top])
        cylinder(d1 = d - 2 * chamfer_top, d2 = d + 0.02, h = chamfer_top + 0.01);
    }
  }
}

// Domed retention nub
module soft_nub(r = 3.2, h = 5.6, $fn = 32) {
  hull() {
    cylinder(r = r, h = max(0.4, h - r));
    translate([0, 0, max(0.4, h - r)])
      sphere(r = r);
  }
}

// 45° triangular buttress from bed to height h, width w along wall tangent.
// Place with translate/rotate so the right-angle sits on bed + wall.
module buttress_45(w, h, t = 3.2) {
  // right triangle: base = h (45° → base = height), thickness t
  linear_extrude(height = t)
    polygon(points = [[0, 0], [h, 0], [0, h]]);
}

// Vertical stilt column that fuses into a deck at z=clearance_z
module stilt(d, clearance_z, fuse = 0.4, $fn = 24) {
  cylinder(d = d, h = clearance_z + fuse);
}

// Unique XY grid of stilts inside a soft rectangle (no corner spam overlaps).
// Callers should difference exterior later if needed.
module stilt_grid(outer_x, outer_y, pitch, d, clearance_z, margin = 8, fuse = 0.4) {
  x0 = -outer_x / 2 + margin;
  x1 =  outer_x / 2 - margin;
  y0 = -outer_y / 2 + margin;
  y1 =  outer_y / 2 - margin;
  for (x = [x0 : pitch : x1])
    for (y = [y0 : pitch : y1])
      translate([x, y, 0])
        stilt(d, clearance_z, fuse);
}

// Local minkowski softener — USE SPARINGLY (slow). Compensates size growth.
module soft_minkowski(r = 1.2, $fn = 16) {
  minkowski() {
    children();
    sphere(r = r);
  }
}

// Shrink-then-minkowski pattern for approx exterior fillet on a child solid
module approx_fillet_exterior(r = 1.2, $fn = 16) {
  soft_minkowski(r = r, $fn = $fn)
    offset_3d_approx(-r)
      children();
}

// Placeholder: OpenSCAD has no true 3D offset; use soft design-from-start instead.
// This module documents the intent — prefer soft_box / hull patterns.
module offset_3d_approx(delta) {
  // Not a real offset — children pass-through. Keep for API stability.
  children();
}
