// =============================================================================
// soft_part_scaffold.scad — soft tray when MIDSPAN FILL is intentional
//
// For DGX-class elevated EQUIPMENT bases use instead:
//   templates/open_frame_equipment_scaffold.scad  (TOP-FIRST, empty under, no stilts)
//
// This scaffold: soft geometry, optional waffle/buttresses, feet-down coords.
// Stilts default OFF (pin forest = aesthetic reject; stand v6 lesson).
// Printer: Bambu Lab P1S · Units: mm
// =============================================================================

/* [Object / pocket] */
object_x = 80;
object_y = 60;
object_z = 25;          // reference height of object (docs)

/* [Fit] */
fit_clearance = 0.8;    // per side
wall = 3.2;
plan_r = 12;            // soft plan fillet

/* [Elevation / deck] */
clearance_z = 20;       // under-air height (0 = flat tray)
deck_t = 3.2;

/* [Soft language] */
bottom_chamfer = 1.2;
nub_enable = true;
nub_r = 3.2;
nub_h = 4.8;
nub_inset = 4;

/* [Print-in-place under-deck] */
// Pin stilts OFF by default — Marc reject on stand v6 ("little cylinders").
// Prefer soft waffle / buttresses when midspan fill is required.
// Equipment with bottom vents: use open_frame_equipment_scaffold instead.
stilts_enable = false;
stilt_d = 2.4;
stilt_pitch = 12;
buttress_enable = true;
buttress_w = 16;
under_ring = 2.4;

/* [Feet] */
foot_recess_d = 12.4;
foot_recess_h = 1.2;
foot_inset = 12;

/* [Quality] */
$fn = 40;
eps = 0.06;

// ---- derived --------------------------------------------------------------
pocket_x = object_x + 2 * fit_clearance;
pocket_y = object_y + 2 * fit_clearance;
outer_margin = max(10, wall + 4);
outer_x = pocket_x + 2 * outer_margin;
outer_y = pocket_y + 2 * outer_margin;
top_z = clearance_z + deck_t;

echo("soft_part_scaffold v2 — soft tray; stilts OFF default; not for DGX open-frame");
echo(str("pocket=", pocket_x, "x", pocket_y, " outer=", outer_x, "x", outer_y));
echo(str("clearance_z=", clearance_z, " stilts=", stilts_enable, " buttress=", buttress_enable));
echo(str("P1S_ok=", (outer_x < 250 && outer_y < 250)));
echo("TIP: equipment bases → open_frame_equipment_scaffold.scad (TOP-FIRST empty under)");

// ---- modules --------------------------------------------------------------
module soft_rect(x, y, r) {
  rr = min(r, min(x, y) / 2 - 0.01);
  offset(r = rr)
    square([x - 2 * rr, y - 2 * rr], center = true);
}

module outer_2d() soft_rect(outer_x, outer_y, plan_r);
module pocket_2d() soft_rect(pocket_x, pocket_y, max(2, plan_r - 4));

module soft_shell() {
  difference() {
    linear_extrude(height = top_z)
      outer_2d();

    // hollow under deck
    if (clearance_z > 0) {
      translate([0, 0, -eps])
        linear_extrude(height = clearance_z + eps)
          offset(r = -wall)
            outer_2d();
    }

    // bottom chamfer
    if (bottom_chamfer > 0) {
      difference() {
        translate([0, 0, -eps])
          linear_extrude(height = bottom_chamfer + eps)
            outer_2d();
        translate([0, 0, -eps])
          linear_extrude(height = bottom_chamfer + 2 * eps)
            offset(r = -bottom_chamfer)
              outer_2d();
      }
    }

    // object pocket in deck
    translate([0, 0, clearance_z + eps])
      linear_extrude(height = deck_t + 1)
        pocket_2d();

    // foot recesses
    for (sx = [-1, 1], sy = [-1, 1])
      translate([
        sx * (outer_x / 2 - foot_inset),
        sy * (outer_y / 2 - foot_inset),
        -eps
      ])
        cylinder(d = foot_recess_d, h = foot_recess_h + eps);
  }
}

module stilts() {
  if (stilts_enable && clearance_z > 0) {
    margin = wall + 4;
    x0 = -outer_x / 2 + margin;
    x1 =  outer_x / 2 - margin;
    y0 = -outer_y / 2 + margin;
    y1 =  outer_y / 2 - margin;
    for (x = [x0 : stilt_pitch : x1])
      for (y = [y0 : stilt_pitch : y1])
        // skip pocket column interior lightly (still OK if under deck ring)
        translate([x, y, 0])
          cylinder(d = stilt_d, h = clearance_z + 0.4);
  }
}

module buttresses() {
  if (buttress_enable && clearance_z > 0) {
    // 8× 45° buttresses: 4 corners + 4 mid-sides (inward facing)
    h = clearance_z;
    t = wall;
    // corners
    for (a = [0, 90, 180, 270])
      rotate([0, 0, a])
        translate([outer_x / 2 - wall, outer_y / 2 - wall, 0])
          rotate([90, 0, -45])
            linear_extrude(height = t)
              polygon([[0, 0], [h, 0], [0, h]]);
    // mid-sides (simplified blocks at 45° via scale)
    for (a = [0, 90, 180, 270])
      rotate([0, 0, a])
        translate([outer_x / 2 - wall, 0, 0])
          rotate([90, 0, 0])
            linear_extrude(height = buttress_w, center = true)
              polygon([[0, 0], [h, 0], [0, h]]);
  }
}

module under_ring_mod() {
  if (under_ring > 0 && clearance_z > 0) {
    translate([0, 0, clearance_z - under_ring])
      linear_extrude(height = under_ring)
        difference() {
          offset(r = -wall)
            outer_2d();
          offset(r = -wall - under_ring)
            outer_2d();
        }
  }
}

module nubs() {
  if (nub_enable) {
    for (sx = [-1, 1], sy = [-1, 1])
      translate([
        sx * (pocket_x / 2 - nub_inset),
        sy * (pocket_y / 2 - nub_inset),
        top_z
      ]) {
        cylinder(r = nub_r, h = max(0.4, nub_h - nub_r));
        translate([0, 0, max(0.4, nub_h - nub_r)])
          sphere(r = nub_r);
      }
  }
}

module part() {
  union() {
    soft_shell();
    stilts();
    buttresses();
    under_ring_mod();
    nubs();
  }
}

part();
