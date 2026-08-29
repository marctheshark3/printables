// Heat-set insert boss — millimetres. Default fastening is heat-set, not printed thread.
// Dimensions: skills/3d-print-openscad/references/heat-set-inserts-fdm.md
// Tag PRINT_SPEC source: datasheet or measured. Assumed insert OD cannot ship
// on fit.required parts.

insert_od_mm = 4.6;          // M3 class major OD, datasheet
insert_hole_d_mm = 4.0;      // recommended FDM hole
insert_depth_mm = 5.7;
boss_od_mm = 8.0;
boss_h_mm = 6.4;
$fn = 48;
eps = 0.02;

module insert_boss() {
  difference() {
    cylinder(d = boss_od_mm, h = boss_h_mm);
    translate([0, 0, -eps])
      cylinder(d = insert_hole_d_mm, h = insert_depth_mm + eps);
  }
}

insert_boss();
