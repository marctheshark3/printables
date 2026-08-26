// =============================================================================
// generative_loadpath.scad — parametric load-path / organic structure demos
// Pure OpenSCAD. Heuristic generative (Tier 0), not FEA/TO.
// Units: mm. Print feet-down.
// =============================================================================

/* [Domain] */
span_x = 120;
depth_y = 28;
height_z = 36;
wall = 3.2;
chord_t = 3.2;

/* [Load-path truss] */
n_bays = 4;
member_d = 3.2;
joint_r = 4.0;
soft_r = 6;

/* [Deck voids] */
hex_r = 5.5;
hex_bar = 2.4;
hex_margin = 8;

/* [Quality] */
$fn = 28;
eps = 0.05;

// --- helpers -----------------------------------------------------------------
module soft_rect(x, y, r) {
  rr = min(r, min(x, y) / 2 - 0.01);
  offset(r = rr)
    square([x - 2 * rr, y - 2 * rr], center = true);
}

module node(p) {
  translate(p) sphere(r = joint_r);
}

module member(a, b, d = member_d) {
  hull() {
    translate(a) sphere(r = d / 2);
    translate(b) sphere(r = d / 2);
  }
}

// Simple bridge truss: top + bottom chords, verticals, 45-ish diagonals
module loadpath_truss() {
  bay = span_x / n_bays;
  z0 = joint_r;
  z1 = height_z - joint_r;
  y = 0;

  // nodes
  for (i = [0 : n_bays]) {
    x = -span_x / 2 + i * bay;
    node([x, y, z0]);
    node([x, y, z1]);
  }

  // chords + verticals + diagonals
  for (i = [0 : n_bays - 1]) {
    x0 = -span_x / 2 + i * bay;
    x1 = x0 + bay;
    // bottom / top chords
    member([x0, y, z0], [x1, y, z0]);
    member([x0, y, z1], [x1, y, z1]);
    // vertical
    member([x1, y, z0], [x1, y, z1]);
    // diagonal (zigzag) — keep angle printable-ish when printed on side;
    // for feet-down bridge print, prefer this as a **side-lying** part or
    // reorient diagonals as buttresses in real projects.
    if (i % 2 == 0)
      member([x0, y, z0], [x1, y, z1]);
    else
      member([x0, y, z1], [x1, y, z0]);
  }
  // left vertical
  member([-span_x / 2, y, z0], [-span_x / 2, y, z1]);
}

// Soft plate with hex voids (organic deck language)
module hex_deck(x, y, t) {
  difference() {
    linear_extrude(height = t)
      soft_rect(x, y, soft_r);
    // hex grid cut
    px = hex_r * sqrt(3) + hex_bar;
    py = hex_r * 1.5 + hex_bar * 0.75;
    for (ix = [-x : px : x], iy = [-y : py : y]) {
      row = round(iy / py);
      xoff = (row % 2) * (px / 2);
      xx = ix + xoff;
      yy = iy;
      if (abs(xx) < x / 2 - hex_margin && abs(yy) < y / 2 - hex_margin)
        translate([xx, yy, -eps])
          linear_extrude(height = t + 2 * eps)
            circle(r = hex_r, $fn = 6);
    }
  }
}

// Branching support: trunk + two 45° arms into deck nodes (print-in-place vibe)
module branch_support(h, spread = 40, d0 = 6, d1 = 2.8) {
  // trunk
  cylinder(d1 = d0, d2 = d1, h = h * 0.55);
  // arms
  for (s = [-1, 1])
    hull() {
      translate([0, 0, h * 0.5]) sphere(d = d1);
      translate([s * spread / 2, 0, h]) sphere(d = d1);
    }
}

// Demo selector
variant = "deck"; // "deck" | "truss" | "branch"

if (variant == "truss") {
  // WARNING: pure mid-air truss may need supports or side print — demo only
  loadpath_truss();
} else if (variant == "branch") {
  branch_support(height_z, spread = span_x * 0.35);
  translate([0, 0, height_z])
    hex_deck(span_x * 0.5, depth_y, chord_t);
} else {
  // default: soft hex deck plate
  hex_deck(span_x, depth_y, chord_t);
}

echo(str("variant=", variant, " span=", span_x, " height=", height_z));
