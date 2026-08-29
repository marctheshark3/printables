// Fit coupon — millimetres. Named parameters must match PRINT_SPEC.yaml.
// One small body, expected_shells = 1. Copy to project fit/<name>-coupon.scad.

hole_d = 4.2;
clearance_per_side_mm = 0.4;
coupon_size_mm = 20;
coupon_z_mm = 3.2;
$fn = 32;
eps = 0.02;

difference() {
  cube([coupon_size_mm, coupon_size_mm, coupon_z_mm]);
  translate([coupon_size_mm / 2, coupon_size_mm / 2, -eps])
    cylinder(d = hole_d + 2 * clearance_per_side_mm, h = coupon_z_mm + 2 * eps);
}
