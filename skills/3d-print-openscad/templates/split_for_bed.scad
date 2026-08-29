// Split-for-bed: two bodies with an alignment pin/socket.
// Units: millimetres. Never scale the part to fit the envelope.
// Copy into the project and set which="a" or which="b" for export.

bar_length_mm = 300;
bar_width_mm = 20;
bar_height_mm = 20;
clearance_per_side_mm = 0.2;
pin_len_mm = 8;
pin_w_mm = 6;
which = "a";  // "a" | "b"
$fn = 32;
eps = 0.02;

half_mm = bar_length_mm / 2;
pin_clear_mm = pin_w_mm + 2 * clearance_per_side_mm;

module bar_half() {
  cube([half_mm, bar_width_mm, bar_height_mm]);
}

module pin() {
  translate([
    half_mm - eps,
    (bar_width_mm - pin_w_mm) / 2,
    (bar_height_mm - pin_w_mm) / 2
  ])
    cube([pin_len_mm + eps, pin_w_mm, pin_w_mm]);
}

module socket() {
  translate([
    -eps,
    (bar_width_mm - pin_clear_mm) / 2,
    (bar_height_mm - pin_clear_mm) / 2
  ])
    cube([pin_len_mm + 2 * eps, pin_clear_mm, pin_clear_mm]);
}

module body_a() {
  union() {
    bar_half();
    pin();
  }
}

module body_b() {
  difference() {
    bar_half();
    socket();
  }
}

if (which == "a")
  body_a();
else
  body_b();
