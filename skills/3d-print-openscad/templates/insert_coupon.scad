// Heat-set insert coupon — millimetres. expected_shells = 1.
// Provenance: references/heat-set-inserts-fdm.md (datasheet).

insert_od_mm = 4.6;
insert_hole_d_mm = 4.0;
insert_depth_mm = 5.7;
boss_od_mm = 8.0;
boss_h_mm = 6.4;
coupon_xy_mm = 20;
coupon_z_mm = 3.2;
$fn = 48;
eps = 0.02;

module insert_boss() {
  difference() {
    cylinder(d = boss_od_mm, h = boss_h_mm);
    translate([0, 0, -eps])
      cylinder(d = insert_hole_d_mm, h = insert_depth_mm + eps);
  }
}

union() {
  cube([coupon_xy_mm, coupon_xy_mm, coupon_z_mm]);
  translate([coupon_xy_mm / 2, coupon_xy_mm / 2, coupon_z_mm - eps])
    insert_boss();
}
