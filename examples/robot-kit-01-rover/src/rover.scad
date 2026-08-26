// robot-kit-01-rover — numbered 01 two-wheel differential chassis.
// Millimetres. Export printable bodies with -D which="chassis"|"wheel"|"head".
// Preview-only: -D which="assembly" (not a printable STL).
use <lib/robot_kit.scad>

which = "chassis";

/* [Chassis] */
chassis_length_mm = 88.0;
chassis_width_mm = 58.0;
deck_thickness_mm = 3.2;
wall_mm = 2.4;

/* [MCU pocket — ESP32-C3 Super Mini class, datasheet] */
mcu_length_mm = 22.5;
mcu_width_mm = 18.0;
mcu_thickness_mm = 3.5;
mcu_pocket_clearance_mm = 0.4;
mcu_pocket_depth_mm = 1.6;

/* [USB-C keepout — see connector-keepouts-fdm.md] */
usb_c_keepout_w_mm = 13.5;
usb_c_keepout_h_mm = 9.0;
usb_c_keepout_d_mm = 12.0;

/* [N20-class gear motor — datasheet] */
motor_gearbox_l_mm = 15.0;
motor_gearbox_w_mm = 12.0;
motor_gearbox_h_mm = 10.0;
motor_shaft_d_mm = 3.0;
motor_shaft_l_mm = 10.0;
motor_pocket_clearance_mm = 0.4;

/* [Photo-class 3-spoke wheel hub — datasheet D-shaft] */
wheel_od_mm = 40.0;
wheel_thickness_mm = 6.0;
wheel_rim_width_mm = 3.2;
spoke_width_mm = 3.2;
spoke_count = 3;
hub_od_mm = 12.0;
wheel_hub_clearance_per_side_mm = 0.15;
wheel_bore_d_mm = 3.3;
wheel_d_flat_mm = 2.8;

/* [M2/M3 ISO 273 medium — datasheet] */
m2_through_d_mm = 2.4;
m3_through_d_mm = 3.4;
m2_boss_od_mm = 5.6;
m3_boss_od_mm = 6.6;
m2_boss_h_mm = 4.0;
m3_boss_h_mm = 6.0;
m3_inset_mm = 6.0;

/* [Head / LED] */
head_od_mm = 24.0;
head_height_mm = 12.0;
led_d_mm = 5.2;
head_boss_od_mm = 10.0;
head_boss_h_mm = 3.2;
head_boss_id_mm = 6.0;

/* [Bought driver / battery envelopes — not printed] */
driver_keepout_z_mm = 3.0;
battery_envelope_h_mm = 6.0;

/* [Cable-path keepouts] */
cable_path_motor_left_w_mm = 4.0;
cable_path_motor_right_w_mm = 4.0;
cable_path_led_w_mm = 4.0;
cable_path_h_mm = 1.6;

/* [Quality] */
quality_fn = 48;
eps_mm = 0.02;

mcu_pocket_l_mm = mcu_length_mm + 2 * mcu_pocket_clearance_mm;
mcu_pocket_w_mm = mcu_width_mm + 2 * mcu_pocket_clearance_mm;
mcu_origin_x = wall_mm + m2_boss_od_mm;
mcu_origin_y = (chassis_width_mm - mcu_pocket_w_mm) / 2;
mcu_center_y = chassis_width_mm / 2;

motor_box_x_mm = motor_gearbox_w_mm + 2 * motor_pocket_clearance_mm + 2 * wall_mm;
motor_box_y_mm = motor_gearbox_l_mm + 2 * motor_pocket_clearance_mm + 2 * wall_mm;
rail_height_mm = deck_thickness_mm + motor_gearbox_h_mm + 2 * motor_pocket_clearance_mm;
motor_center_x = mcu_origin_x + mcu_pocket_l_mm + wall_mm + motor_box_x_mm / 2;
head_x = chassis_length_mm - wall_mm - head_boss_od_mm / 2;

module chassis() {
  difference() {
    union() {
      cube([chassis_length_mm, chassis_width_mm, deck_thickness_mm]);
      cube([wall_mm, chassis_width_mm, deck_thickness_mm + usb_c_keepout_h_mm]);
      translate([motor_center_x - motor_box_x_mm / 2, 0, 0])
        cube([motor_box_x_mm, motor_box_y_mm, rail_height_mm]);
      translate([motor_center_x - motor_box_x_mm / 2, chassis_width_mm - motor_box_y_mm, 0])
        cube([motor_box_x_mm, motor_box_y_mm, rail_height_mm]);
      translate([head_x, mcu_center_y, 0])
        cylinder(d=head_boss_od_mm, h=deck_thickness_mm + head_boss_h_mm, $fn=quality_fn);
      translate([m3_inset_mm, m3_inset_mm, 0])
        cylinder(d=m3_boss_od_mm, h=m3_boss_h_mm, $fn=quality_fn);
      translate([chassis_length_mm - m3_inset_mm, m3_inset_mm, 0])
        cylinder(d=m3_boss_od_mm, h=m3_boss_h_mm, $fn=quality_fn);
      translate([m3_inset_mm, chassis_width_mm - m3_inset_mm, 0])
        cylinder(d=m3_boss_od_mm, h=m3_boss_h_mm, $fn=quality_fn);
      translate([chassis_length_mm - m3_inset_mm, chassis_width_mm - m3_inset_mm, 0])
        cylinder(d=m3_boss_od_mm, h=m3_boss_h_mm, $fn=quality_fn);
      translate([mcu_origin_x + m2_boss_od_mm / 2, mcu_origin_y - m2_boss_od_mm / 2, 0])
        cylinder(d=m2_boss_od_mm, h=m2_boss_h_mm, $fn=quality_fn);
      translate([mcu_origin_x + mcu_pocket_l_mm - m2_boss_od_mm / 2, mcu_origin_y - m2_boss_od_mm / 2, 0])
        cylinder(d=m2_boss_od_mm, h=m2_boss_h_mm, $fn=quality_fn);
      translate([mcu_origin_x + m2_boss_od_mm / 2, mcu_origin_y + mcu_pocket_w_mm + m2_boss_od_mm / 2, 0])
        cylinder(d=m2_boss_od_mm, h=m2_boss_h_mm, $fn=quality_fn);
      translate([mcu_origin_x + mcu_pocket_l_mm - m2_boss_od_mm / 2, mcu_origin_y + mcu_pocket_w_mm + m2_boss_od_mm / 2, 0])
        cylinder(d=m2_boss_od_mm, h=m2_boss_h_mm, $fn=quality_fn);
    }
    translate([mcu_origin_x, mcu_origin_y, deck_thickness_mm - mcu_pocket_depth_mm])
      mcu_pocket_void(
        mcu_length_mm, mcu_width_mm, mcu_pocket_depth_mm + mcu_thickness_mm,
        mcu_pocket_clearance_mm, eps_mm
      );
    translate([-eps_mm, mcu_center_y - usb_c_keepout_w_mm / 2, deck_thickness_mm - mcu_pocket_depth_mm])
      cube([usb_c_keepout_d_mm + eps_mm, usb_c_keepout_w_mm, usb_c_keepout_h_mm]);
    translate([motor_center_x, wall_mm, deck_thickness_mm])
      n20_motor_pocket_void(
        motor_gearbox_l_mm, motor_gearbox_w_mm, motor_gearbox_h_mm,
        motor_shaft_d_mm, motor_shaft_l_mm, motor_pocket_clearance_mm,
        eps_mm, quality_fn
      );
    translate([motor_center_x, chassis_width_mm - wall_mm, deck_thickness_mm])
      mirror([0, 1, 0])
        n20_motor_pocket_void(
          motor_gearbox_l_mm, motor_gearbox_w_mm, motor_gearbox_h_mm,
          motor_shaft_d_mm, motor_shaft_l_mm, motor_pocket_clearance_mm,
          eps_mm, quality_fn
        );
    translate([
      mcu_origin_x + mcu_pocket_l_mm,
      mcu_center_y - cable_path_led_w_mm / 2,
      deck_thickness_mm - cable_path_h_mm
    ])
      cube([
        head_x - (mcu_origin_x + mcu_pocket_l_mm),
        cable_path_led_w_mm,
        cable_path_h_mm + eps_mm
      ]);
    translate([
      motor_center_x - cable_path_motor_left_w_mm / 2,
      motor_box_y_mm,
      deck_thickness_mm - cable_path_h_mm
    ])
      cube([
        cable_path_motor_left_w_mm,
        mcu_center_y - motor_box_y_mm,
        cable_path_h_mm + eps_mm
      ]);
    translate([
      motor_center_x - cable_path_motor_right_w_mm / 2,
      mcu_center_y,
      deck_thickness_mm - cable_path_h_mm
    ])
      cube([
        cable_path_motor_right_w_mm,
        mcu_center_y - motor_box_y_mm,
        cable_path_h_mm + eps_mm
      ]);
    translate([m3_inset_mm, m3_inset_mm, 0])
      m3_through_hole(m3_boss_h_mm, m3_through_d_mm, eps_mm, quality_fn);
    translate([chassis_length_mm - m3_inset_mm, m3_inset_mm, 0])
      m3_through_hole(m3_boss_h_mm, m3_through_d_mm, eps_mm, quality_fn);
    translate([m3_inset_mm, chassis_width_mm - m3_inset_mm, 0])
      m3_through_hole(m3_boss_h_mm, m3_through_d_mm, eps_mm, quality_fn);
    translate([chassis_length_mm - m3_inset_mm, chassis_width_mm - m3_inset_mm, 0])
      m3_through_hole(m3_boss_h_mm, m3_through_d_mm, eps_mm, quality_fn);
    translate([mcu_origin_x + m2_boss_od_mm / 2, mcu_origin_y - m2_boss_od_mm / 2, 0])
      m2_through_hole(m2_boss_h_mm, m2_through_d_mm, eps_mm, quality_fn);
    translate([mcu_origin_x + mcu_pocket_l_mm - m2_boss_od_mm / 2, mcu_origin_y - m2_boss_od_mm / 2, 0])
      m2_through_hole(m2_boss_h_mm, m2_through_d_mm, eps_mm, quality_fn);
    translate([mcu_origin_x + m2_boss_od_mm / 2, mcu_origin_y + mcu_pocket_w_mm + m2_boss_od_mm / 2, 0])
      m2_through_hole(m2_boss_h_mm, m2_through_d_mm, eps_mm, quality_fn);
    translate([mcu_origin_x + mcu_pocket_l_mm - m2_boss_od_mm / 2, mcu_origin_y + mcu_pocket_w_mm + m2_boss_od_mm / 2, 0])
      m2_through_hole(m2_boss_h_mm, m2_through_d_mm, eps_mm, quality_fn);
    translate([head_x, mcu_center_y, 0])
      through_hole(head_boss_id_mm, deck_thickness_mm + head_boss_h_mm, eps_mm, quality_fn);
  }
}

module wheel() {
  wheel_3spoke(
    wheel_od_mm, wheel_thickness_mm, wheel_rim_width_mm, hub_od_mm,
    wheel_bore_d_mm, wheel_d_flat_mm, spoke_width_mm, spoke_count,
    eps_mm, quality_fn
  );
}

module head() {
  difference() {
    hull() {
      cylinder(d=head_od_mm, h=wall_mm, $fn=quality_fn);
      translate([0, 0, head_height_mm - wall_mm])
        cylinder(d=led_d_mm + 2 * wall_mm, h=wall_mm, $fn=quality_fn);
    }
    translate([0, 0, -eps_mm])
      cylinder(d=led_d_mm, h=head_height_mm + 2 * eps_mm, $fn=quality_fn);
  }
}

wheel_axis_z = deck_thickness_mm + motor_gearbox_h_mm / 2;
assembly_lift_mm = wheel_od_mm / 2 - wheel_axis_z;

module bought_mcu() {
  translate([
    mcu_origin_x + mcu_pocket_clearance_mm,
    mcu_origin_y + mcu_pocket_clearance_mm,
    deck_thickness_mm - mcu_pocket_depth_mm
  ])
    cube([mcu_length_mm, mcu_width_mm, mcu_thickness_mm]);
}

module bought_n20_left() {
  gx = motor_gearbox_w_mm;
  gy = motor_gearbox_l_mm;
  gz = motor_gearbox_h_mm;
  translate([motor_center_x - gx / 2, wall_mm + motor_pocket_clearance_mm, deck_thickness_mm])
    cube([gx, gy, gz]);
  translate([motor_center_x, wall_mm, wheel_axis_z])
    rotate([90, 0, 0])
      cylinder(d=motor_shaft_d_mm, h=motor_shaft_l_mm, $fn=quality_fn);
}

module bought_n20_right() {
  gx = motor_gearbox_w_mm;
  gy = motor_gearbox_l_mm;
  gz = motor_gearbox_h_mm;
  translate([
    motor_center_x - gx / 2,
    chassis_width_mm - wall_mm - motor_pocket_clearance_mm - gy,
    deck_thickness_mm
  ])
    cube([gx, gy, gz]);
  translate([motor_center_x, chassis_width_mm - wall_mm, wheel_axis_z])
    rotate([-90, 0, 0])
      cylinder(d=motor_shaft_d_mm, h=motor_shaft_l_mm, $fn=quality_fn);
}

module bought_led() {
  translate([head_x, mcu_center_y, deck_thickness_mm + head_boss_h_mm + head_height_mm - 2])
    cylinder(d=led_d_mm - 0.4, h=4, $fn=quality_fn);
}

module assembly() {
  translate([0, 0, assembly_lift_mm]) {
    color("#2B2B2B") chassis();
    color("#1A1A1A") {
      translate([motor_center_x, 0, wheel_axis_z])
        rotate([90, 0, 0])
          wheel();
      translate([motor_center_x, chassis_width_mm, wheel_axis_z])
        rotate([-90, 0, 0])
          wheel();
    }
    color("#3A3A3A")
      translate([head_x, mcu_center_y, deck_thickness_mm + head_boss_h_mm])
        head();
    color("#1B5E20") bought_mcu();
    color("#9E9E9E") {
      bought_n20_left();
      bought_n20_right();
    }
    color("#D32F2F") bought_led();
  }
}

if (which == "chassis") chassis();
else if (which == "wheel") wheel();
else if (which == "head") head();
else if (which == "assembly") assembly();
