// =============================================================================
// pip_hinge_cones.scad — print-in-place interlocking cone hinge (pure OpenSCAD)
// Horizontal axis along +X. Print feet-down with hinge axis // bed.
// Tune pip_gap for your P1S / material (start 0.35–0.45).
// =============================================================================

/* [Hinge] */
leaf_len = 40;       // along hinge axis (X)
leaf_w = 18;         // Y extent of each leaf
leaf_t = 3.2;        // thickness of leaves
segs = 5;            // odd recommended
cone_h = 4.0;        // segment axial length
cone_r_outer = 4.0;
cone_r_inner = 2.0;
pip_gap = 0.40;      // diametral-ish clearance budget
axial_gap = 0.20;
round_edge = 0.8;

$fn = 48;
eps = 0.05;

// --- cone segment ------------------------------------------------------------
module cone_male(h, r0, r1) {
  cylinder(h = h, r1 = r0, r2 = r1);
}

module cone_female_void(h, r0, r1, gap) {
  // slightly larger inverse cone cavity
  translate([0, 0, -eps])
    cylinder(h = h + 2 * eps, r1 = r0 + gap / 2, r2 = r1 + gap / 2);
}

// Leaf plate (soft edges via hull)
module leaf_plate(sign_y) {
  // sign_y: -1 = back leaf, +1 = front leaf
  translate([0, sign_y * (leaf_w / 2 + cone_r_outer * 0.15), 0])
    hull() {
      translate([-leaf_len / 2 + round_edge, -sign_y * leaf_w / 2 + round_edge, 0])
        cylinder(r = round_edge, h = leaf_t);
      translate([ leaf_len / 2 - round_edge, -sign_y * leaf_w / 2 + round_edge, 0])
        cylinder(r = round_edge, h = leaf_t);
      translate([-leaf_len / 2 + round_edge,  sign_y * leaf_w / 2 - round_edge, 0])
        cylinder(r = round_edge, h = leaf_t);
      translate([ leaf_len / 2 - round_edge,  sign_y * leaf_w / 2 - round_edge, 0])
        cylinder(r = round_edge, h = leaf_t);
    }
}

module hinge_assembly() {
  pitch = cone_h + axial_gap;
  total = segs * pitch;
  // center along X
  x0 = -total / 2;

  // leaves
  color("SteelBlue") leaf_plate(-1);
  color("CadetBlue") leaf_plate(+1);

  // alternating cone stacks on axis at y=0, z = leaf_t/2 level for printability
  // axis along X at (y=0, z=cone_r_outer)
  for (i = [0 : segs - 1]) {
    male = (i % 2 == 0);
    translate([x0 + i * pitch, 0, cone_r_outer])
      rotate([0, 90, 0]) {
        if (male) {
          // male cone fused to -Y leaf via a neck
          union() {
            cone_male(cone_h, cone_r_outer, cone_r_inner);
            // neck to -Y leaf
            translate([0, 0, cone_h / 2])
              rotate([90, 0, 0])
                cylinder(d = cone_r_inner * 1.2, h = leaf_w / 2);
          }
        } else {
          // female ring fused to +Y leaf
          difference() {
            union() {
              cylinder(h = cone_h, r = cone_r_outer + 1.2);
              translate([0, 0, cone_h / 2])
                rotate([-90, 0, 0])
                  cylinder(d = cone_r_inner * 1.2, h = leaf_w / 2);
            }
            cone_female_void(cone_h, cone_r_outer, cone_r_inner, pip_gap);
          }
        }
      }
  }
}

echo(str("pip_gap=", pip_gap, " segs=", segs, " leaf_len=", leaf_len));
hinge_assembly();
