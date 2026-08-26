// Parametric printable part scaffold — units: mm
// Copy to project src/, rename modules, fill geometry.

/* [Target object] */
object_x = 100;
object_y = 100;
object_z = 20;       // reference only unless used

/* [Fit / structure] */
fit_clearance = 0.8;
wall = 3.2;
deck_thick = 4.0;
clearance_z = 20;    // open height under deck if elevated

/* [Feet] */
foot_recess_d = 12.4;
foot_recess_h = 1.2;
foot_inset = 12;

/* [Quality] */
$fn = 48;
eps = 0.02;

// Derived
pocket_x = object_x + 2 * fit_clearance;
pocket_y = object_y + 2 * fit_clearance;
outer_x = pocket_x + 2 * 10;
outer_y = pocket_y + 2 * 10;

module outer_footprint() {
  offset(r = 6)
    square([outer_x - 12, outer_y - 12], center = true);
}

module part() {
  difference() {
    union() {
      // TODO: skirt / body
      linear_extrude(height = clearance_z + deck_thick)
        outer_footprint();
    }
    // hollow interior example
    translate([0, 0, -eps])
      linear_extrude(height = clearance_z + eps)
        offset(r = -wall)
          outer_footprint();
    // foot recesses
    for (sx = [-1, 1], sy = [-1, 1])
      translate([sx * (outer_x / 2 - foot_inset),
                 sy * (outer_y / 2 - foot_inset),
                 -eps])
        cylinder(d = foot_recess_d, h = foot_recess_h + eps);
  }
}

echo(str("outer_xy=", outer_x, "x", outer_y));
echo(str("P1S_fit_xy=", (outer_x < 250 && outer_y < 250)));

part();
