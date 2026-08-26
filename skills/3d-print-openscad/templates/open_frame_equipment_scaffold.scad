// =============================================================================
// open_frame_equipment_scaffold.scad — DEFAULT for DGX-class elevated bases
// Pattern proven on dgx-spark-stand v9 (skill regression gold).
//
// Design law:
//   - Soft hex (or solid-margin) seating deck ONLY under device
//   - EMPTY under-volume (no waffle, no pin stilts)
//   - Perimeter soft pillars + optional windowed skirt + thin edge beam
//   - Open rear for I/O
//   - TOP-FIRST print: Z=0 = rim top (bed) → build toward feet free end
//   - Use: flip → feet desk, pocket up
//
// Printer: Bambu Lab P1S · Units: mm · OpenSCAD 2021.01 hermetic
// Copy to <project>/src/<part>.scad and edit named parameters.
// =============================================================================

/* [Chassis / object] */
chassis_x = 150;
chassis_y = 150;
// chassis_z for docs only (Spark 50.5) — not modeled solid by default
chassis_z_ref = 50.5;

/* [Fit] */
fit_clearance = 0.8;
lip_h = 5.6;            // pocket depth (rim height on bed)
lip_t = 2.8;            // rim wall thickness toward pocket
corner_pad = 6;         // soft corner locators inside pocket (not free posts)

/* [Elevation] */
clearance_z = 35;       // EMPTY under-air under deck
deck_t = 3.2;
wall = 3.6;
outer_margin = 14;
plan_r = 18;

/* [Hex deck — seating surface only] */
hex_r = 5.5;
hex_bar = 2.4;
hex_rim = 10;           // solid margin under chassis edge

/* [Open frame — NO waffle, NO stilts] */
pillar_w = 16;
pillar_soft = 4;
edge_beam_w = 8;
edge_beam_h = 3.2;
window_enable = true;
window_margin = 18;
window_r = 10;

/* [Feet] */
foot_pad_r = 10;
foot_pad_h = 2.0;
foot_recess_d = 12.4;
foot_recess_h = 1.2;
foot_inset = 12;

/* [Rear I/O] */
rear_open_frac = 0.78;

/* [Chamfers] */
bed_chamfer = 0.8;
foot_chamfer = 1.2;

/* [Quality] */
$fn = 32;
eps = 0.06;

// ---------------------------------------------------------------------------
// Print Z: 0 = rim top (bed) → pocket → deck → empty air → feet free end
// ---------------------------------------------------------------------------
pocket_x = chassis_x + 2 * fit_clearance;
pocket_y = chassis_y + 2 * fit_clearance;
outer_x = pocket_x + 2 * outer_margin;
outer_y = pocket_y + 2 * outer_margin;

z_deck_top = lip_h;
z_deck_under = lip_h + deck_t;
z_feet = z_deck_under + clearance_z;

hex_px = hex_r * sqrt(3) + hex_bar;
hex_py = hex_r * 1.5 + hex_bar * 0.75;

echo("OPEN FRAME equipment scaffold — empty under device, hex deck only");
echo(str("pocket=", pocket_x, "x", pocket_y, " outer=", outer_x, "x", outer_y));
echo(str("clearance_z=", clearance_z, " pillar_w=", pillar_w, " NO waffle NO stilts"));
echo(str("z_feet=", z_feet, " P1S_ok=", (outer_x < 250 && outer_y < 250)));
echo("PRINT: TOP-FIRST rim on bed · USE: flip feet-down");

module soft_rect(x, y, r) {
  r2 = min(r, min(x, y) / 2 - eps);
  offset(r = r2)
    square([x - 2 * r2, y - 2 * r2], center = true);
}
module outer_2d() soft_rect(outer_x, outer_y, plan_r);
module pocket_2d() soft_rect(pocket_x, pocket_y, max(2, plan_r - 6));
module hex(r) circle(r = r, $fn = 6);
module capsule_2d(len, r) {
  hull() {
    translate([-len / 2 + r, 0]) circle(r = r);
    translate([ len / 2 - r, 0]) circle(r = r);
  }
}

module tray_rim() {
  difference() {
    linear_extrude(height = lip_h)
      difference() {
        outer_2d();
        offset(r = -lip_t)
          pocket_2d();
      }
    translate([0, 0, -eps])
      linear_extrude(height = lip_h + 2 * eps)
        pocket_2d();
    if (bed_chamfer > 0) {
      difference() {
        translate([0, 0, -eps])
          linear_extrude(height = bed_chamfer + eps)
            outer_2d();
        translate([0, 0, -eps])
          linear_extrude(height = bed_chamfer + 2 * eps)
            offset(r = -bed_chamfer)
              outer_2d();
      }
    }
    rw = outer_y * rear_open_frac;
    translate([outer_x / 2 - outer_margin * 0.55, 0, lip_h / 2])
      cube([outer_margin + 8, rw, lip_h + 2], center = true);
  }
  for (sx = [-1, 1], sy = [-1, 1])
    translate([
      sx * (pocket_x / 2 - corner_pad),
      sy * (pocket_y / 2 - corner_pad),
      0
    ])
      cylinder(r = corner_pad * 0.55, h = lip_h);
}

module hex_deck() {
  translate([0, 0, z_deck_top])
    difference() {
      linear_extrude(height = deck_t)
        outer_2d();
      nx = ceil(pocket_x / hex_px) + 2;
      ny = ceil(pocket_y / hex_py) + 2;
      for (iy = [-ny : ny])
        for (ix = [-nx : nx]) {
          ox = (iy % 2 == 0) ? 0 : hex_px / 2;
          cx = ix * hex_px + ox;
          cy = iy * hex_py;
          if (abs(cx) < pocket_x / 2 - hex_rim &&
              abs(cy) < pocket_y / 2 - hex_rim)
            translate([cx, cy, -eps])
              linear_extrude(height = deck_t + 2 * eps)
                hex(hex_r);
        }
      rw = outer_y * rear_open_frac * 0.85;
      translate([outer_x / 2 - outer_margin * 0.5, 0, deck_t / 2])
        cube([outer_margin + 6, rw, deck_t + 2], center = true);
    }
}

module edge_beam() {
  translate([0, 0, z_deck_under - eps])
    linear_extrude(height = edge_beam_h + eps)
      difference() {
        offset(r = -wall + 0.2)
          outer_2d();
        offset(r = -wall - edge_beam_w)
          outer_2d();
        rw = outer_y * rear_open_frac * 0.9;
        translate([outer_x / 2 - wall, 0])
          square([wall * 4, rw], center = true);
      }
}

module corner_pillar(rot) {
  w = pillar_w;
  h = clearance_z;
  rotate([0, 0, rot])
    translate([-outer_x / 2 + wall * 0.15, -outer_y / 2 + wall * 0.15, z_deck_under])
      hull() {
        translate([pillar_soft, pillar_soft, 0])
          cylinder(r = pillar_soft, h = 1.2);
        translate([w - pillar_soft, pillar_soft, 0])
          cylinder(r = pillar_soft, h = 1.2);
        translate([pillar_soft, w - pillar_soft, 0])
          cylinder(r = pillar_soft, h = 1.2);
        translate([pillar_soft + 1, pillar_soft + 1, h - 0.8])
          cylinder(r = pillar_soft + 0.5, h = 0.8);
        translate([w * 0.55, pillar_soft + 1, h - 0.8])
          cylinder(r = pillar_soft, h = 0.8);
        translate([pillar_soft + 1, w * 0.55, h - 0.8])
          cylinder(r = pillar_soft, h = 0.8);
      }
}

module all_pillars() {
  for (r = [0, 90, 180, 270])
    corner_pillar(r);
}

module open_skirt() {
  difference() {
    translate([0, 0, z_deck_under])
      linear_extrude(height = clearance_z)
        difference() {
          outer_2d();
          offset(r = -wall)
            outer_2d();
        }
    rw = outer_y * rear_open_frac;
    translate([outer_x / 2 - wall / 2, 0, z_deck_under + clearance_z / 2])
      cube([wall + 10, rw, clearance_z + 2], center = true);
    if (window_enable) {
      zw = z_deck_under + clearance_z * 0.5;
      wh = clearance_z * 0.72;
      translate([-(outer_x / 2 - wall / 2), 0, zw])
        rotate([90, 0, 90])
          linear_extrude(height = wall + 6, center = true)
            capsule_2d(outer_y - 2 * window_margin, min(window_r, wh / 2));
      translate([0, outer_y / 2 - wall / 2, zw])
        rotate([90, 0, 0])
          linear_extrude(height = wall + 6, center = true)
            capsule_2d(outer_x - 2 * window_margin, min(window_r, wh / 2));
      translate([0, -(outer_y / 2 - wall / 2), zw])
        rotate([90, 0, 0])
          linear_extrude(height = wall + 6, center = true)
            capsule_2d(outer_x - 2 * window_margin, min(window_r, wh / 2));
    }
    if (foot_chamfer > 0) {
      translate([0, 0, z_feet - foot_chamfer])
        difference() {
          linear_extrude(height = foot_chamfer + eps)
            outer_2d();
          linear_extrude(height = foot_chamfer + 2 * eps)
            offset(r = -foot_chamfer)
              outer_2d();
        }
    }
  }
}

module foot_pads() {
  corners = [
    [ outer_x / 2 - foot_inset,  outer_y / 2 - foot_inset],
    [ outer_x / 2 - foot_inset, -outer_y / 2 + foot_inset],
    [-outer_x / 2 + foot_inset,  outer_y / 2 - foot_inset],
    [-outer_x / 2 + foot_inset, -outer_y / 2 + foot_inset]
  ];
  for (p = corners)
    translate([p[0], p[1], z_feet])
      cylinder(r = foot_pad_r, h = foot_pad_h);
}

module foot_recesses() {
  corners = [
    [ outer_x / 2 - foot_inset,  outer_y / 2 - foot_inset],
    [ outer_x / 2 - foot_inset, -outer_y / 2 + foot_inset],
    [-outer_x / 2 + foot_inset,  outer_y / 2 - foot_inset],
    [-outer_x / 2 + foot_inset, -outer_y / 2 + foot_inset]
  ];
  for (p = corners)
    translate([p[0], p[1], z_feet + foot_pad_h - foot_recess_h])
      cylinder(d = foot_recess_d, h = foot_recess_h + eps);
}

module open_frame_equipment() {
  difference() {
    union() {
      tray_rim();
      hex_deck();
      edge_beam();
      all_pillars();
      open_skirt();
      foot_pads();
    }
    foot_recesses();
  }
}

open_frame_equipment();
