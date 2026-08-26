// robot-kit-01-rover-v2 — numbered 01 rover with SG90 pan and HC-SR04.
// Millimetres. Export with -D which="chassis"|"wheel"|"sensor_bracket".
use <lib/robot_kit.scad>

which = "chassis";

/* [Chassis] */
chassis_length_mm = 108.0;
chassis_width_mm = 62.0;
deck_thickness_mm = 3.2;
wall_mm = 2.4;

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

/* [N20-class gear motor — datasheet] */
motor_gearbox_l_mm = 15.0;
motor_gearbox_w_mm = 12.0;
motor_gearbox_h_mm = 10.0;
motor_shaft_d_mm = 3.0;
motor_shaft_l_mm = 10.0;
motor_pocket_clearance_mm = 0.4;

/* [Photo-class 3-spoke wheel] */
wheel_od_mm = 40.0;
wheel_thickness_mm = 6.0;
wheel_rim_width_mm = 3.2;
spoke_width_mm = 3.2;
spoke_count = 3;
hub_od_mm = 12.0;
wheel_hub_clearance_per_side_mm = 0.15;
wheel_bore_d_mm = 3.3;
wheel_d_flat_mm = 2.8;

/* [SG90 / 9g micro servo — datasheet class] */
sg90_body_x_mm = 22.8;
sg90_body_y_mm = 12.2;
sg90_body_z_mm = 22.8;
sg90_tab_span_mm = 32.3;
sg90_tab_thick_mm = 2.5;
sg90_tab_width_mm = 12.0;
sg90_pocket_clearance_mm = 0.4;
sg90_horn_radius_mm = 20.0;
sg90_horn_clearance_h_mm = 6.0;

/* [HC-SR04 carrier — datasheet class] */
bracket_length_mm = 46.0;
bracket_width_mm = 22.0;
bracket_thickness_mm = 3.2;
transducer_d_mm = 16.4;
transducer_spacing_mm = 26.0;
horn_boss_od_mm = 10.0;
horn_boss_h_mm = 3.2;
horn_boss_id_mm = 2.4;
horn_stack_mm = 2.4;

/* [MPU-6050 class IMU pad] */
imu_length_mm = 21.0;
imu_width_mm = 16.0;
imu_thickness_mm = 3.5;
imu_pocket_depth_mm = 1.2;

/* [M2/M3 ISO 273 medium] */
m2_through_d_mm = 2.4;
m3_through_d_mm = 3.4;
m2_boss_od_mm = 5.6;
m3_boss_od_mm = 6.6;
m2_boss_h_mm = 4.0;
m3_boss_h_mm = 6.0;
m3_inset_mm = 6.0;

/* [Bought envelopes — not printed] */
driver_keepout_z_mm = 3.0;
battery_envelope_h_mm = 6.0;
ultrasonic_h_mm = 15.0;

/* [Cable-path keepouts] */
cable_path_motor_left_w_mm = 4.0;
cable_path_motor_right_w_mm = 4.0;
cable_path_servo_w_mm = 4.0;
cable_path_imu_w_mm = 4.0;
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

servo_house_x_mm = sg90_tab_span_mm + 2 * sg90_pocket_clearance_mm + 2 * wall_mm;
servo_house_y_mm = sg90_body_y_mm + 2 * sg90_pocket_clearance_mm + 2 * wall_mm;
servo_house_h_mm = deck_thickness_mm + sg90_body_z_mm;
servo_center_x = chassis_length_mm - wall_mm - sg90_tab_span_mm / 2;

imu_origin_x = motor_center_x + motor_box_x_mm / 2 + wall_mm;
imu_origin_y = wall_mm;

module chassis() {
  difference() {
    union() {
      cube([chassis_length_mm, chassis_width_mm, deck_thickness_mm]);
      cube([wall_mm, chassis_width_mm, deck_thickness_mm + usb_c_keepout_h_mm]);
      translate([motor_center_x - motor_box_x_mm / 2, 0, 0])
        cube([motor_box_x_mm, motor_box_y_mm, rail_height_mm]);
      translate([motor_center_x - motor_box_x_mm / 2, chassis_width_mm - motor_box_y_mm, 0])
        cube([motor_box_x_mm, motor_box_y_mm, rail_height_mm]);
      translate([servo_center_x - servo_house_x_mm / 2, mcu_center_y - servo_house_y_mm / 2, 0])
        cube([servo_house_x_mm, servo_house_y_mm, servo_house_h_mm]);
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
    translate([servo_center_x, mcu_center_y, deck_thickness_mm])
      sg90_pocket_void(
        sg90_body_x_mm, sg90_body_y_mm, sg90_body_z_mm,
        sg90_tab_span_mm, sg90_tab_thick_mm, sg90_tab_width_mm,
        sg90_pocket_clearance_mm, eps_mm
      );
    translate([servo_center_x, mcu_center_y, deck_thickness_mm + sg90_body_z_mm])
      sg90_horn_clearance_void(sg90_horn_radius_mm, sg90_horn_clearance_h_mm, quality_fn, eps_mm);
    translate([imu_origin_x, imu_origin_y, deck_thickness_mm - imu_pocket_depth_mm])
      cube([imu_length_mm, imu_width_mm, imu_pocket_depth_mm + eps_mm]);
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
    translate([
      mcu_origin_x + mcu_pocket_l_mm,
      mcu_center_y - cable_path_servo_w_mm / 2,
      deck_thickness_mm - cable_path_h_mm
    ])
      cube([
        servo_center_x - (mcu_origin_x + mcu_pocket_l_mm),
        cable_path_servo_w_mm,
        cable_path_h_mm + eps_mm
      ]);
    translate([
      imu_origin_x - cable_path_imu_w_mm,
      mcu_center_y - cable_path_imu_w_mm / 2,
      deck_thickness_mm - cable_path_h_mm
    ])
      cube([cable_path_imu_w_mm, cable_path_imu_w_mm, cable_path_h_mm + eps_mm]);
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
  }
}

module wheel() {
  wheel_3spoke(
    wheel_od_mm, wheel_thickness_mm, wheel_rim_width_mm, hub_od_mm,
    wheel_bore_d_mm, wheel_d_flat_mm, spoke_width_mm, spoke_count,
    eps_mm, quality_fn
  );
}

module sensor_bracket() {
  // Plate on bed, boss up (print, no supports). Vertical face looks +X.
  difference() {
    union() {
      translate([-bracket_width_mm / 2, -bracket_width_mm / 2, 0])
        cube([
          bracket_width_mm + bracket_thickness_mm,
          bracket_width_mm,
          bracket_thickness_mm
        ]);
      cylinder(
        d=horn_boss_od_mm, h=bracket_thickness_mm + horn_boss_h_mm, $fn=quality_fn
      );
      translate([bracket_width_mm / 2, -bracket_length_mm / 2, 0])
        cube([bracket_thickness_mm, bracket_length_mm, bracket_width_mm]);
    }
    through_hole(
      horn_boss_id_mm, bracket_thickness_mm + horn_boss_h_mm, eps_mm, quality_fn
    );
    translate([
      bracket_width_mm / 2 - eps_mm,
      -transducer_spacing_mm / 2,
      bracket_width_mm / 2
    ])
      rotate([0, 90, 0])
        cylinder(
          d=transducer_d_mm, h=bracket_thickness_mm + 2 * eps_mm, $fn=quality_fn
        );
    translate([
      bracket_width_mm / 2 - eps_mm,
      transducer_spacing_mm / 2,
      bracket_width_mm / 2
    ])
      rotate([0, 90, 0])
        cylinder(
          d=transducer_d_mm, h=bracket_thickness_mm + 2 * eps_mm, $fn=quality_fn
        );
  }
}

if (which == "chassis") chassis();
else if (which == "wheel") wheel();
else if (which == "sensor_bracket") sensor_bracket();
