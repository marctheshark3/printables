// robot-kit-03-pendulum desk — inverted pendulum, horizontal SG90 shaft.
// Stick sweeps a vertical plane. No lid, no collar. Cream rod, red ball.
// Millimetres. Export -D which="plate"|"stick"|"knob".
// Preview-only: -D which="assembly".
use <lib/robot_kit.scad>

which = "plate";

/* [Desk plate] */
plate_l_mm = 104.0;
plate_w_mm = 56.0;
plate_t_mm = 4.0;
plate_r_mm = 16.0;
wall_mm = 2.4;
fairing_l_mm = 50.0;
fairing_w_mm = 38.0;
fairing_h_mm = 26.0;
fairing_r_mm = 12.0;
fairing_nose_mm = 0.0;
chin_h_mm = 8.0;

/* [Shaft — horizontal, Y; stick in XZ] */
shaft_x_mm = 70.0;
shaft_front_mm = 7.0;
shaft_y_mm = -shaft_front_mm;
shaft_z_mm = 16.0;

/* [MCU pocket — ESP32-C3 Super Mini class, datasheet] */
mcu_length_mm = 22.5;
mcu_width_mm = 18.0;
mcu_thickness_mm = 3.5;
mcu_pocket_clearance_mm = 0.4;
mcu_pocket_depth_mm = 1.6;

/* [USB-C keepout] */
usb_c_keepout_w_mm = 13.5;
usb_c_keepout_h_mm = 9.0;
usb_c_keepout_d_mm = 12.0;

/* [SG90 / 9g micro servo — datasheet class] */
sg90_body_x_mm = 22.8;
sg90_body_y_mm = 12.2;
sg90_body_z_mm = 22.8;
sg90_tab_span_mm = 32.3;
sg90_tab_thick_mm = 2.5;
sg90_tab_width_mm = 12.0;
sg90_pocket_clearance_mm = 0.4;
sg90_horn_radius_mm = 16.0;
sg90_horn_clearance_h_mm = 6.0;

/* [Stick / knob — cream rod, red ball] */
stick_h_mm = 52.0;
stick_base_d_mm = 8.0;
stick_tip_d_mm = 4.8;
knob_d_mm = 16.0;
knob_flat_mm = 3.2;
horn_boss_od_mm = 10.0;
horn_id_mm = 2.4;
hub_h_mm = 8.0;
preview_from_rest_deg = 72.0;

/* [M2/M3 ISO 273 medium — datasheet] */
m2_through_d_mm = 2.4;
m3_through_d_mm = 3.4;
m2_boss_od_mm = 5.6;
m3_boss_od_mm = 6.6;
m2_boss_h_mm = 4.0;
m3_boss_h_mm = 6.0;
m3_inset_mm = 12.0;

/* [Bought envelopes — not printed] */
battery_envelope_h_mm = 6.0;

/* [Cable-path keepouts] */
cable_path_servo_w_mm = 4.0;
cable_path_h_mm = 1.6;

/* [Number stamp] */
number_size_mm = 12.0;
number_depth_mm = 0.8;

/* [Quality] */
quality_fn = 48;
eps_mm = 0.02;

desk_mcu_pocket_l_mm = mcu_length_mm + 2 * mcu_pocket_clearance_mm;
desk_mcu_pocket_w_mm = mcu_width_mm + 2 * mcu_pocket_clearance_mm;
desk_mcu_ox = wall_mm + m2_boss_od_mm;
desk_mcu_oy = 14.0;
desk_mcu_cy = desk_mcu_oy + desk_mcu_pocket_w_mm / 2;
desk_fairing_x = shaft_x_mm - fairing_l_mm / 2;
desk_fairing_y = 0.0;
desk_open_w_mm = sg90_tab_span_mm + 2 * wall_mm;
desk_stick_tip_mm = hub_h_mm / 2 + stick_h_mm;

module desk_number_stamp(txt) {
  linear_extrude(height=number_depth_mm + eps_mm)
    text(txt, size=number_size_mm, font="Liberation Sans:style=Bold",
         halign="center", valign="center", $fn=quality_fn);
}

module desk_rounded_profile(l, w, r) {
  rr = min(r, l / 2 - 0.01, w / 2 - 0.01);
  translate([rr, rr])
    offset(r=rr)
      square([l - 2 * rr, w - 2 * rr]);
}

module desk_rounded_prism(l, w, h, r) {
  linear_extrude(height=h)
    desk_rounded_profile(l, w, r);
}

module desk_sg90_on_side() {
  // Shaft along -Y at origin, body in +Y. Pocket matches sg90_pocket_void.
  rotate([90, 0, 0])
    translate([0, 0, -sg90_body_z_mm])
      sg90_pocket_void(
        sg90_body_x_mm, sg90_body_y_mm, sg90_body_z_mm,
        sg90_tab_span_mm, sg90_tab_thick_mm, sg90_tab_width_mm,
        sg90_pocket_clearance_mm, eps_mm
      );
}

module desk_plate() {
  difference() {
    union() {
      desk_rounded_prism(plate_l_mm, plate_w_mm, plate_t_mm, plate_r_mm);
      // Low rounded fairing around the servo on the plate. Stick lives in front (y<0).
      translate([desk_fairing_x, desk_fairing_y, 0])
        desk_rounded_prism(fairing_l_mm, fairing_w_mm, fairing_h_mm, fairing_r_mm);
      translate([desk_mcu_ox + m2_boss_od_mm / 2, desk_mcu_oy - m2_boss_od_mm / 2, 0])
        cylinder(d=m2_boss_od_mm, h=m2_boss_h_mm, $fn=quality_fn);
      translate([desk_mcu_ox + desk_mcu_pocket_l_mm - m2_boss_od_mm / 2, desk_mcu_oy - m2_boss_od_mm / 2, 0])
        cylinder(d=m2_boss_od_mm, h=m2_boss_h_mm, $fn=quality_fn);
      translate([desk_mcu_ox + m2_boss_od_mm / 2, desk_mcu_oy + desk_mcu_pocket_w_mm + m2_boss_od_mm / 2, 0])
        cylinder(d=m2_boss_od_mm, h=m2_boss_h_mm, $fn=quality_fn);
      translate([desk_mcu_ox + desk_mcu_pocket_l_mm - m2_boss_od_mm / 2, desk_mcu_oy + desk_mcu_pocket_w_mm + m2_boss_od_mm / 2, 0])
        cylinder(d=m2_boss_od_mm, h=m2_boss_h_mm, $fn=quality_fn);
    }
    // Interior of fairing, leave wall_mm shell. Chin under the shaft stays.
    translate([
      desk_fairing_x + wall_mm,
      desk_fairing_y + wall_mm,
      plate_t_mm
    ])
      desk_rounded_prism(
        fairing_l_mm - 2 * wall_mm,
        fairing_w_mm - 2 * wall_mm,
        fairing_h_mm,
        max(1.6, fairing_r_mm - wall_mm)
      );
    // Open the entire front of the fairing so the rod is never collared.
    translate([
      shaft_x_mm - desk_open_w_mm / 2,
      desk_fairing_y - eps_mm,
      chin_h_mm
    ])
      cube([desk_open_w_mm, fairing_nose_mm + wall_mm + 4.0, fairing_h_mm]);
    translate([shaft_x_mm, shaft_y_mm, shaft_z_mm])
      desk_sg90_on_side();
    translate([desk_mcu_ox, desk_mcu_oy, plate_t_mm - mcu_pocket_depth_mm])
      mcu_pocket_void(
        mcu_length_mm, mcu_width_mm, mcu_pocket_depth_mm + mcu_thickness_mm,
        mcu_pocket_clearance_mm, eps_mm
      );
    translate([-eps_mm, desk_mcu_cy - usb_c_keepout_w_mm / 2, plate_t_mm - mcu_pocket_depth_mm])
      cube([usb_c_keepout_d_mm + eps_mm, usb_c_keepout_w_mm, usb_c_keepout_h_mm]);
    translate([
      desk_mcu_ox + desk_mcu_pocket_l_mm,
      desk_mcu_cy - cable_path_servo_w_mm / 2,
      plate_t_mm - cable_path_h_mm
    ])
      cube([
        shaft_x_mm - (desk_mcu_ox + desk_mcu_pocket_l_mm),
        cable_path_servo_w_mm,
        cable_path_h_mm + eps_mm
      ]);
    translate([m3_inset_mm, m3_inset_mm, 0])
      m3_through_hole(plate_t_mm, m3_through_d_mm, eps_mm, quality_fn);
    translate([plate_l_mm - m3_inset_mm, m3_inset_mm, 0])
      m3_through_hole(plate_t_mm, m3_through_d_mm, eps_mm, quality_fn);
    translate([m3_inset_mm, plate_w_mm - m3_inset_mm, 0])
      m3_through_hole(plate_t_mm, m3_through_d_mm, eps_mm, quality_fn);
    translate([plate_l_mm - m3_inset_mm, plate_w_mm - m3_inset_mm, 0])
      m3_through_hole(plate_t_mm, m3_through_d_mm, eps_mm, quality_fn);
    translate([desk_mcu_ox + m2_boss_od_mm / 2, desk_mcu_oy - m2_boss_od_mm / 2, 0])
      m2_through_hole(m2_boss_h_mm, m2_through_d_mm, eps_mm, quality_fn);
    translate([desk_mcu_ox + desk_mcu_pocket_l_mm - m2_boss_od_mm / 2, desk_mcu_oy - m2_boss_od_mm / 2, 0])
      m2_through_hole(m2_boss_h_mm, m2_through_d_mm, eps_mm, quality_fn);
    translate([desk_mcu_ox + m2_boss_od_mm / 2, desk_mcu_oy + desk_mcu_pocket_w_mm + m2_boss_od_mm / 2, 0])
      m2_through_hole(m2_boss_h_mm, m2_through_d_mm, eps_mm, quality_fn);
    translate([desk_mcu_ox + desk_mcu_pocket_l_mm - m2_boss_od_mm / 2, desk_mcu_oy + desk_mcu_pocket_w_mm + m2_boss_od_mm / 2, 0])
      m2_through_hole(m2_boss_h_mm, m2_through_d_mm, eps_mm, quality_fn);
    // 03 on the front of the plate / fairing, facing the user.
    translate([shaft_x_mm, number_depth_mm, chin_h_mm * 0.55 + 3.0])
      rotate([90, 0, 0])
        desk_number_stamp("03");
  }
}

module desk_stick() {
  // Print: hub on the bed, rod up +Z. Shaft hole along Y (bridged).
  // Assembly: rpy [0,-90,0] sends the rod along world -X, hole along Y.
  difference() {
    union() {
      translate([0, 0, -hub_h_mm / 2])
        cylinder(d=horn_boss_od_mm, h=hub_h_mm, $fn=quality_fn);
      translate([0, 0, hub_h_mm / 2 - 0.4])
        cylinder(d1=stick_base_d_mm, d2=stick_tip_d_mm, h=stick_h_mm + 0.4, $fn=quality_fn);
    }
    rotate([90, 0, 0])
      translate([0, 0, -horn_boss_od_mm / 2])
        through_hole(horn_id_mm, horn_boss_od_mm, eps_mm, quality_fn);
  }
}

module desk_stick_print() {
  translate([0, 0, hub_h_mm / 2])
    desk_stick();
}

module desk_knob() {
  difference() {
    translate([0, 0, knob_d_mm / 2 - knob_flat_mm])
      sphere(d=knob_d_mm, $fn=quality_fn);
    translate([-knob_d_mm, -knob_d_mm, -knob_d_mm])
      cube([2 * knob_d_mm, 2 * knob_d_mm, knob_d_mm]);
    translate([0, 0, -eps_mm])
      cylinder(d=stick_tip_d_mm + 0.4, h=knob_d_mm, $fn=quality_fn);
  }
}

module desk_bought_mcu() {
  translate([
    desk_mcu_ox + mcu_pocket_clearance_mm,
    desk_mcu_oy + mcu_pocket_clearance_mm,
    plate_t_mm - mcu_pocket_depth_mm
  ])
    cube([mcu_length_mm, mcu_width_mm, mcu_thickness_mm]);
}

module desk_bought_sg90() {
  translate([shaft_x_mm, shaft_y_mm, shaft_z_mm])
    rotate([90, 0, 0])
      translate([-sg90_body_x_mm / 2, -sg90_body_y_mm / 2, -sg90_body_z_mm])
        cube([sg90_body_x_mm, sg90_body_y_mm, sg90_body_z_mm]);
}

module desk_ground() {
  translate([-28, -40, -0.8])
    cube([plate_l_mm + 56, plate_w_mm + 80, 0.8]);
}

module desk_sweep_wedge() {
  // Thin 180° rim in the vertical XZ plane — a clear arc, not a lid.
  color("#C62828", 0.35)
    translate([shaft_x_mm, shaft_y_mm, shaft_z_mm])
      rotate([90, 0, 0]) {
        rotate_extrude(angle=180, $fn=quality_fn)
          translate([stick_h_mm + knob_d_mm / 2 - 3.4, -0.3])
            square([2.4, 0.6]);
        for (a = [0, 90, 180])
          rotate([0, 0, a])
            translate([hub_h_mm / 2 + 8.0, -0.3, 0])
              cube([stick_h_mm + knob_d_mm / 2 - 3.4 - (hub_h_mm / 2 + 8.0), 0.6, 0.6]);
      }
}

module desk_placed_stick() {
  translate([shaft_x_mm, shaft_y_mm, shaft_z_mm])
    rotate([0, -90 + preview_from_rest_deg, 0])
      desk_stick();
}

module desk_placed_knob() {
  translate([shaft_x_mm, shaft_y_mm, shaft_z_mm])
    rotate([0, -90 + preview_from_rest_deg, 0])
      translate([0, 0, desk_stick_tip_mm])
        desk_knob();
}

module pendulum_assembly() {
  color("#1C1C1C") desk_plate();
  color("#D7CCC8") desk_placed_stick();
  color("#C62828") desk_placed_knob();
  color("#1B5E20") desk_bought_mcu();
  color("#9E9E9E") desk_bought_sg90();
  desk_sweep_wedge();
  color("#C8C0B4") desk_ground();
}

module assembly() {
  pendulum_assembly();
}

if (which == "plate") desk_plate();
else if (which == "stick") desk_stick_print();
else if (which == "knob") desk_knob();
else if (which == "assembly") assembly();
