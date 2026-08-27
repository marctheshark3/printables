// robot-kit-03-pendulum wall — same inverted pendulum, plate hangs on a wall.
// Stick swings in front of the wall, vertical plane parallel to the wall.
// USB-C out the bottom. Two M3 keyholes + two lower M3 holes.
// Millimetres. Export -D which="wall_plate"|"stick"|"knob".
// Preview-only: -D which="assembly".
use <lib/robot_kit.scad>

which = "wall_plate";

/* [Wall plate — assembled: X left-right, Y out from wall, Z up] */
plate_l_mm = 104.0;
plate_h_mm = 88.0;
plate_t_mm = 4.0;
plate_r_mm = 16.0;
wall_mm = 2.4;
fairing_l_mm = 44.0;
fairing_w_mm = 24.0;
fairing_h_mm = 36.0;
fairing_r_mm = 12.0;
keyhole_head_d_mm = 6.6;
keyhole_drop_mm = 8.0;

/* [Shaft — horizontal, Y (out from wall); stick in XZ parallel to wall] */
shaft_x_mm = 70.0;
shaft_y_mm = 32.0;
shaft_z_mm = 50.0;

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

/* [Stick / knob — cream rod, red ball. Same as desk 03.] */
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

wall_mcu_pocket_l_mm = mcu_length_mm + 2 * mcu_pocket_clearance_mm;
wall_mcu_pocket_w_mm = mcu_width_mm + 2 * mcu_pocket_clearance_mm;
// MCU on the front face, USB out the bottom (-Z). Length along X, width along Z.
wall_mcu_ox = wall_mm + m2_boss_od_mm;
wall_mcu_oz = 6.0;
wall_mcu_cx = wall_mcu_ox + wall_mcu_pocket_l_mm / 2;
wall_fairing_x = shaft_x_mm - fairing_l_mm / 2;
wall_fairing_z = shaft_z_mm - fairing_h_mm / 2;
wall_open_w_mm = sg90_tab_span_mm + 2 * wall_mm;
wall_stick_tip_mm = hub_h_mm / 2 + stick_h_mm;
wall_key_z = plate_h_mm - m3_inset_mm;

module wall_number_stamp(txt) {
  linear_extrude(height=number_depth_mm + eps_mm)
    text(txt, size=number_size_mm, font="Liberation Sans:style=Bold",
         halign="center", valign="center", $fn=quality_fn);
}

module wall_rounded_profile(l, w, r) {
  rr = min(r, l / 2 - 0.01, w / 2 - 0.01);
  translate([rr, rr])
    offset(r=rr)
      square([l - 2 * rr, w - 2 * rr]);
}

module wall_rounded_prism(l, w, h, r) {
  linear_extrude(height=h)
    wall_rounded_profile(l, w, r);
}

module wall_sg90_on_side() {
  // Shaft along +Y at origin (out from wall), body in -Y toward the plate.
  rotate([-90, 0, 0])
    translate([0, 0, -sg90_body_z_mm])
      sg90_pocket_void(
        sg90_body_x_mm, sg90_body_y_mm, sg90_body_z_mm,
        sg90_tab_span_mm, sg90_tab_thick_mm, sg90_tab_width_mm,
        sg90_pocket_clearance_mm, eps_mm
      );
}

module wall_keyhole() {
  // M3 keyhole in the Y (through-plate) direction. Head circle + drop slot.
  rotate([90, 0, 0]) {
    translate([0, 0, -eps_mm])
      cylinder(d=keyhole_head_d_mm, h=plate_t_mm + 2 * eps_mm, $fn=quality_fn);
    translate([0, -keyhole_drop_mm, -eps_mm])
      cylinder(d=m3_through_d_mm, h=plate_t_mm + 2 * eps_mm, $fn=quality_fn);
    translate([-m3_through_d_mm / 2, -keyhole_drop_mm, -eps_mm])
      cube([m3_through_d_mm, keyhole_drop_mm, plate_t_mm + 2 * eps_mm]);
  }
}

module wall_plate_assembled() {
  difference() {
    union() {
      // Plate in XZ, thickness +Y (out from the wall at Y=0).
      rotate([90, 0, 0])
        translate([0, 0, -plate_t_mm])
          wall_rounded_prism(plate_l_mm, plate_h_mm, plate_t_mm, plate_r_mm);
      // Servo fairing on the FRONT, behind the stick.
      translate([wall_fairing_x, 0, wall_fairing_z])
        rotate([90, 0, 0])
          translate([0, 0, -fairing_w_mm])
            wall_rounded_prism(fairing_l_mm, fairing_h_mm, fairing_w_mm, fairing_r_mm);
      translate([wall_mcu_ox + m2_boss_od_mm / 2, 0, wall_mcu_oz - m2_boss_od_mm / 2])
        rotate([-90, 0, 0])
          cylinder(d=m2_boss_od_mm, h=m2_boss_h_mm, $fn=quality_fn);
      translate([wall_mcu_ox + wall_mcu_pocket_l_mm - m2_boss_od_mm / 2, 0, wall_mcu_oz - m2_boss_od_mm / 2])
        rotate([-90, 0, 0])
          cylinder(d=m2_boss_od_mm, h=m2_boss_h_mm, $fn=quality_fn);
      translate([wall_mcu_ox + m2_boss_od_mm / 2, 0, wall_mcu_oz + wall_mcu_pocket_w_mm + m2_boss_od_mm / 2])
        rotate([-90, 0, 0])
          cylinder(d=m2_boss_od_mm, h=m2_boss_h_mm, $fn=quality_fn);
      translate([wall_mcu_ox + wall_mcu_pocket_l_mm - m2_boss_od_mm / 2, 0, wall_mcu_oz + wall_mcu_pocket_w_mm + m2_boss_od_mm / 2])
        rotate([-90, 0, 0])
          cylinder(d=m2_boss_od_mm, h=m2_boss_h_mm, $fn=quality_fn);
    }
    // Fairing cavity, leave wall_mm. Front (+Y) open so the stick is free.
    translate([
      wall_fairing_x + wall_mm,
      plate_t_mm,
      wall_fairing_z + wall_mm
    ])
      cube([
        fairing_l_mm - 2 * wall_mm,
        fairing_w_mm,
        fairing_h_mm - 2 * wall_mm
      ]);
    translate([
      shaft_x_mm - wall_open_w_mm / 2,
      shaft_y_mm - 6.0,
      shaft_z_mm - 10.0
    ])
      cube([wall_open_w_mm, 20.0, 20.0]);
    translate([shaft_x_mm, shaft_y_mm, shaft_z_mm])
      wall_sg90_on_side();
    // MCU well in the front face. USB-C out the bottom, not into the wall.
    translate([
      wall_mcu_ox,
      plate_t_mm - mcu_pocket_depth_mm,
      wall_mcu_oz + wall_mcu_pocket_w_mm
    ])
      rotate([-90, 0, 0])
        mcu_pocket_void(
          mcu_length_mm, mcu_width_mm, mcu_pocket_depth_mm + mcu_thickness_mm,
          mcu_pocket_clearance_mm, eps_mm
        );
    translate([
      wall_mcu_cx - usb_c_keepout_w_mm / 2,
      plate_t_mm - mcu_pocket_depth_mm,
      -eps_mm
    ])
      cube([usb_c_keepout_w_mm, usb_c_keepout_h_mm, usb_c_keepout_d_mm + eps_mm]);
    translate([
      wall_mcu_ox + wall_mcu_pocket_l_mm,
      plate_t_mm - cable_path_h_mm,
      wall_mcu_oz + wall_mcu_pocket_w_mm / 2 - cable_path_servo_w_mm / 2
    ])
      cube([
        shaft_x_mm - (wall_mcu_ox + wall_mcu_pocket_l_mm),
        cable_path_h_mm + eps_mm,
        cable_path_servo_w_mm
      ]);
    translate([m3_inset_mm, plate_t_mm, wall_key_z])
      wall_keyhole();
    translate([plate_l_mm - m3_inset_mm, plate_t_mm, wall_key_z])
      wall_keyhole();
    translate([m3_inset_mm, 0, m3_inset_mm])
      rotate([-90, 0, 0])
        m3_through_hole(plate_t_mm, m3_through_d_mm, eps_mm, quality_fn);
    translate([plate_l_mm - m3_inset_mm, 0, m3_inset_mm])
      rotate([-90, 0, 0])
        m3_through_hole(plate_t_mm, m3_through_d_mm, eps_mm, quality_fn);
    translate([wall_mcu_ox + m2_boss_od_mm / 2, 0, wall_mcu_oz - m2_boss_od_mm / 2])
      rotate([-90, 0, 0])
        m2_through_hole(m2_boss_h_mm, m2_through_d_mm, eps_mm, quality_fn);
    translate([wall_mcu_ox + wall_mcu_pocket_l_mm - m2_boss_od_mm / 2, 0, wall_mcu_oz - m2_boss_od_mm / 2])
      rotate([-90, 0, 0])
        m2_through_hole(m2_boss_h_mm, m2_through_d_mm, eps_mm, quality_fn);
    translate([wall_mcu_ox + m2_boss_od_mm / 2, 0, wall_mcu_oz + wall_mcu_pocket_w_mm + m2_boss_od_mm / 2])
      rotate([-90, 0, 0])
        m2_through_hole(m2_boss_h_mm, m2_through_d_mm, eps_mm, quality_fn);
    translate([wall_mcu_ox + wall_mcu_pocket_l_mm - m2_boss_od_mm / 2, 0, wall_mcu_oz + wall_mcu_pocket_w_mm + m2_boss_od_mm / 2])
      rotate([-90, 0, 0])
        m2_through_hole(m2_boss_h_mm, m2_through_d_mm, eps_mm, quality_fn);
    // 03 on the front of the fairing.
    translate([shaft_x_mm, fairing_w_mm + eps_mm, wall_fairing_z + 8.0])
      rotate([90, 0, 180])
        wall_number_stamp("03");
  }
}

module wall_plate_print() {
  // Back on the bed, crib up. Invert of assembly rpy [-90,0,0] + z=plate_h.
  translate([0, plate_h_mm, 0])
    rotate([90, 0, 0])
      wall_plate_assembled();
}

module wall_stick() {
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

module wall_stick_print() {
  translate([0, 0, hub_h_mm / 2])
    wall_stick();
}

module wall_knob() {
  difference() {
    translate([0, 0, knob_d_mm / 2 - knob_flat_mm])
      sphere(d=knob_d_mm, $fn=quality_fn);
    translate([-knob_d_mm, -knob_d_mm, -knob_d_mm])
      cube([2 * knob_d_mm, 2 * knob_d_mm, knob_d_mm]);
    translate([0, 0, -eps_mm])
      cylinder(d=stick_tip_d_mm + 0.4, h=knob_d_mm, $fn=quality_fn);
  }
}

module wall_bought_mcu() {
  translate([
    wall_mcu_ox + mcu_pocket_clearance_mm,
    plate_t_mm - mcu_pocket_depth_mm,
    wall_mcu_oz + mcu_pocket_clearance_mm
  ])
    cube([mcu_length_mm, mcu_thickness_mm, mcu_width_mm]);
}

module wall_bought_sg90() {
  translate([shaft_x_mm, shaft_y_mm, shaft_z_mm])
    rotate([-90, 0, 0])
      translate([-sg90_body_x_mm / 2, -sg90_body_y_mm / 2, -sg90_body_z_mm])
        cube([sg90_body_x_mm, sg90_body_y_mm, sg90_body_z_mm]);
}

module wall_plane() {
  color("#D9D0C4")
    translate([-48, -2.4, -28])
      cube([plate_l_mm + 96, 2.4, plate_h_mm + 72]);
}

module wall_sweep_wedge() {
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

module wall_placed_stick() {
  translate([shaft_x_mm, shaft_y_mm, shaft_z_mm])
    rotate([0, -90 + preview_from_rest_deg, 0])
      wall_stick();
}

module wall_placed_knob() {
  translate([shaft_x_mm, shaft_y_mm, shaft_z_mm])
    rotate([0, -90 + preview_from_rest_deg, 0])
      translate([0, 0, wall_stick_tip_mm])
        wall_knob();
}

module pendulum_wall_assembly() {
  wall_plane();
  color("#1C1C1C") wall_plate_assembled();
  color("#D7CCC8") wall_placed_stick();
  color("#C62828") wall_placed_knob();
  color("#1B5E20") wall_bought_mcu();
  color("#9E9E9E") wall_bought_sg90();
  wall_sweep_wedge();
}

module assembly() {
  pendulum_wall_assembly();
}

if (which == "wall_plate") wall_plate_print();
else if (which == "stick") wall_stick_print();
else if (which == "knob") wall_knob();
else if (which == "assembly") assembly();
