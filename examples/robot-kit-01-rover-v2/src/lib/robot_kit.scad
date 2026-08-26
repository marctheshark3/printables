// robot_kit.scad — shared millimetre modules for numbered FDM robotics kits.
// OpenSCAD 2021.01. No unexplained numeric literals in geometry.
// Copy to <project>/src/lib/robot_kit.scad for hermetic Docker export.
//
// Provenance (tag the same source on PRINT_SPEC hardware.interfaces):
//   ESP32-C3 Super Mini class: ~22.5 x 18 mm, 2.54 mm pitch, USB-C on a short
//   edge, 3.3 V GPIO / 5 V USB (datasheet class, WeAct/generic Super Mini).
//   SG90 / 9g: body ~22.8 x 12.2 x 22.8 mm, tab span ~32.3 mm; vendor drawings
//   disagree, so pocket clearance must be datasheet, measured, or fit-tested.
//   M2/M3 through holes: ISO 273 medium series.
//   Photo-class wheel: 3-spoke hub for a 3 mm D-shaft N20-class motor.
// USB / connector window sizes: 3d-print-openscad/references/connector-keepouts-fdm.md
// (do not copy a second keepout table into this file).
// Buy, do not print: motors, batteries, MCUs, servos, bearings, extrusion frames.

module mcu_pocket_void(length_mm, width_mm, depth_mm, clearance_per_side_mm, eps_mm) {
  assert(length_mm > 0 && width_mm > 0 && depth_mm > 0);
  cube([
    length_mm + 2 * clearance_per_side_mm,
    width_mm + 2 * clearance_per_side_mm,
    depth_mm + eps_mm
  ]);
}

module usb_keepout_void(width_mm, height_mm, depth_mm, eps_mm) {
  assert(width_mm > 0 && height_mm > 0 && depth_mm > 0);
  translate([-width_mm / 2, -eps_mm, 0])
    cube([width_mm, depth_mm + eps_mm, height_mm]);
}

module sg90_pocket_void(
  body_x_mm, body_y_mm, body_z_mm,
  tab_span_mm, tab_thick_mm, tab_width_mm,
  clearance_per_side_mm, eps_mm
) {
  assert(body_x_mm > 0 && body_y_mm > 0 && body_z_mm > 0);
  assert(tab_span_mm >= body_x_mm && tab_thick_mm > 0 && tab_width_mm > 0);
  body_x = body_x_mm + 2 * clearance_per_side_mm;
  body_y = body_y_mm + 2 * clearance_per_side_mm;
  body_z = body_z_mm + eps_mm;
  tab_x = tab_span_mm + 2 * clearance_per_side_mm;
  tab_y = tab_width_mm + 2 * clearance_per_side_mm;
  tab_z = tab_thick_mm + 2 * clearance_per_side_mm;
  translate([-body_x / 2, -body_y / 2, 0])
    cube([body_x, body_y, body_z]);
  translate([-tab_x / 2, -tab_y / 2, body_z_mm - tab_thick_mm - clearance_per_side_mm])
    cube([tab_x, tab_y, tab_z]);
}

module sg90_horn_clearance_void(radius_mm, height_mm, quality_fn, eps_mm) {
  assert(radius_mm > 0 && height_mm > 0);
  translate([0, 0, -eps_mm])
    cylinder(r=radius_mm, h=height_mm + 2 * eps_mm, $fn=quality_fn);
}

module through_hole(d_mm, h_mm, eps_mm, quality_fn) {
  assert(d_mm > 0 && h_mm > 0);
  translate([0, 0, -eps_mm])
    cylinder(d=d_mm, h=h_mm + 2 * eps_mm, $fn=quality_fn);
}

module fastener_boss(od_mm, id_mm, h_mm, eps_mm, quality_fn) {
  assert(od_mm > id_mm && id_mm > 0 && h_mm > 0);
  difference() {
    cylinder(d=od_mm, h=h_mm, $fn=quality_fn);
    through_hole(id_mm, h_mm, eps_mm, quality_fn);
  }
}

module m2_through_hole(h_mm, through_d_mm, eps_mm, quality_fn) {
  through_hole(through_d_mm, h_mm, eps_mm, quality_fn);
}

module m3_through_hole(h_mm, through_d_mm, eps_mm, quality_fn) {
  through_hole(through_d_mm, h_mm, eps_mm, quality_fn);
}

module m2_boss(h_mm, od_mm, through_d_mm, eps_mm, quality_fn) {
  fastener_boss(od_mm, through_d_mm, h_mm, eps_mm, quality_fn);
}

module m3_boss(h_mm, od_mm, through_d_mm, eps_mm, quality_fn) {
  fastener_boss(od_mm, through_d_mm, h_mm, eps_mm, quality_fn);
}

module n20_motor_pocket_void(
  gearbox_l_mm, gearbox_w_mm, gearbox_h_mm,
  shaft_d_mm, shaft_l_mm, clearance_per_side_mm, eps_mm, quality_fn
) {
  assert(gearbox_l_mm > 0 && gearbox_w_mm > 0 && gearbox_h_mm > 0);
  gx = gearbox_w_mm + 2 * clearance_per_side_mm;
  gy = gearbox_l_mm + 2 * clearance_per_side_mm;
  gz = gearbox_h_mm + 2 * clearance_per_side_mm;
  translate([-gx / 2, 0, 0])
    cube([gx, gy, gz + eps_mm]);
  translate([0, -shaft_l_mm, gearbox_h_mm / 2])
    rotate([-90, 0, 0])
      cylinder(d=shaft_d_mm + 2 * clearance_per_side_mm, h=shaft_l_mm + gy + eps_mm, $fn=quality_fn);
}

module cable_channel_void(width_mm, height_mm, length_mm, eps_mm) {
  assert(width_mm > 0 && height_mm > 0 && length_mm > 0);
  translate([-width_mm / 2, 0, -height_mm])
    cube([width_mm, length_mm, height_mm + eps_mm]);
}

module d_shaft_void(bore_d_mm, d_flat_mm, h_mm, eps_mm, quality_fn) {
  assert(bore_d_mm > 0 && d_flat_mm > 0 && d_flat_mm <= bore_d_mm);
  intersection() {
    translate([0, 0, -eps_mm])
      cylinder(d=bore_d_mm, h=h_mm + 2 * eps_mm, $fn=quality_fn);
    translate([-bore_d_mm, -d_flat_mm / 2, -eps_mm])
      cube([2 * bore_d_mm, d_flat_mm + bore_d_mm, h_mm + 2 * eps_mm]);
  }
}

module wheel_3spoke(
  od_mm, thickness_mm, rim_width_mm, hub_od_mm,
  bore_d_mm, d_flat_mm, spoke_width_mm, spoke_count,
  eps_mm, quality_fn
) {
  assert(od_mm > hub_od_mm && hub_od_mm > bore_d_mm);
  assert(rim_width_mm > 0 && spoke_width_mm > 0 && spoke_count >= 3);
  difference() {
    linear_extrude(height=thickness_mm)
      difference() {
        circle(d=od_mm, $fn=quality_fn);
        difference() {
          circle(d=od_mm - 2 * rim_width_mm, $fn=quality_fn);
          circle(d=hub_od_mm, $fn=quality_fn);
          for (i = [0:spoke_count - 1])
            rotate(i * 360 / spoke_count)
              square([spoke_width_mm, od_mm], center=true);
        }
      }
    d_shaft_void(bore_d_mm, d_flat_mm, thickness_mm, eps_mm, quality_fn);
  }
}
