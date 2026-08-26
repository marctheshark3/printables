// robot-kit-03-gimbal — numbered 03 pan/tilt joystick gimbal body.
// Millimetres. Export -D which="base"|"yoke"|"stick"|"knob".
// Preview-only: -D which="assembly".
// Same MCU pocket family as 01/02. Not an inverted-pendulum stick.
use <lib/robot_kit.scad>

which = "base";

/* [Base plate] */
plate_mm = 76.0;
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

/* [Stick / knob] */
stick_h_mm = 48.0;
stick_base_d_mm = 8.0;
stick_tip_d_mm = 3.6;
knob_d_mm = 10.0;
knob_flat_mm = 2.4;
horn_boss_od_mm = 10.0;
horn_id_mm = 2.4;
horn_pad_h_mm = 3.2;

/* [M2/M3 ISO 273 medium — datasheet] */
m2_through_d_mm = 2.4;
m3_through_d_mm = 3.4;
m2_boss_od_mm = 5.6;
m3_boss_od_mm = 6.6;
m2_boss_h_mm = 4.0;
m3_boss_h_mm = 6.0;
m3_inset_mm = 6.0;

/* [Bought envelopes — not printed] */
battery_envelope_h_mm = 6.0;

/* [Cable-path keepouts] */
cable_path_pan_w_mm = 4.0;
cable_path_tilt_w_mm = 4.0;
cable_path_h_mm = 1.6;

/* [Number stamp] */
number_size_mm = 9.0;
number_depth_mm = 0.8;

/* [Quality] */
quality_fn = 48;
eps_mm = 0.02;

mcu_pocket_l_mm = mcu_length_mm + 2 * mcu_pocket_clearance_mm;
mcu_pocket_w_mm = mcu_width_mm + 2 * mcu_pocket_clearance_mm;
mcu_origin_x = plate_mm - wall_mm - mcu_pocket_l_mm;
mcu_origin_y = (plate_mm - mcu_pocket_w_mm) / 2;
mcu_center_y = mcu_origin_y + mcu_pocket_w_mm / 2;

servo_house_x_mm = sg90_tab_span_mm + 2 * sg90_pocket_clearance_mm + 2 * wall_mm;
servo_house_y_mm = sg90_body_y_mm + 2 * sg90_pocket_clearance_mm + 2 * wall_mm;
servo_house_h_mm = deck_thickness_mm + sg90_body_z_mm + 2 * sg90_pocket_clearance_mm;
pan_center_x = wall_mm + servo_house_x_mm / 2;
pan_center_y = plate_mm / 2;

module number_stamp(txt) {
  linear_extrude(height=number_depth_mm + eps_mm)
    text(txt, size=number_size_mm, font="Liberation Sans:style=Bold",
         halign="center", valign="center", $fn=quality_fn);
}

module base() {
  difference() {
    union() {
      cube([plate_mm, plate_mm, deck_thickness_mm]);
      translate([pan_center_x, pan_center_y, 0])
        translate([-servo_house_x_mm / 2, -servo_house_y_mm / 2, 0])
          cube([servo_house_x_mm, servo_house_y_mm, servo_house_h_mm]);
      translate([plate_mm - wall_mm, mcu_origin_y - wall_mm, 0])
        cube([wall_mm, mcu_pocket_w_mm + 2 * wall_mm, deck_thickness_mm + usb_c_keepout_h_mm]);
      translate([m3_inset_mm, m3_inset_mm, 0])
        cylinder(d=m3_boss_od_mm, h=m3_boss_h_mm, $fn=quality_fn);
      translate([plate_mm - m3_inset_mm, m3_inset_mm, 0])
        cylinder(d=m3_boss_od_mm, h=m3_boss_h_mm, $fn=quality_fn);
      translate([m3_inset_mm, plate_mm - m3_inset_mm, 0])
        cylinder(d=m3_boss_od_mm, h=m3_boss_h_mm, $fn=quality_fn);
      translate([plate_mm - m3_inset_mm, plate_mm - m3_inset_mm, 0])
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
    translate([
      plate_mm - usb_c_keepout_d_mm,
      mcu_center_y - usb_c_keepout_w_mm / 2,
      deck_thickness_mm - mcu_pocket_depth_mm
    ])
      cube([usb_c_keepout_d_mm + eps_mm, usb_c_keepout_w_mm, usb_c_keepout_h_mm]);
    translate([pan_center_x, pan_center_y, deck_thickness_mm])
      sg90_pocket_void(
        sg90_body_x_mm, sg90_body_y_mm, sg90_body_z_mm,
        sg90_tab_span_mm, sg90_tab_thick_mm, sg90_tab_width_mm,
        sg90_pocket_clearance_mm, eps_mm
      );
    translate([pan_center_x, pan_center_y, deck_thickness_mm + sg90_body_z_mm])
      sg90_horn_clearance_void(sg90_horn_radius_mm, sg90_horn_clearance_h_mm, quality_fn, eps_mm);
    translate([
      pan_center_x + servo_house_x_mm / 2,
      pan_center_y - cable_path_pan_w_mm / 2,
      deck_thickness_mm - cable_path_h_mm
    ])
      cube([
        mcu_origin_x - (pan_center_x + servo_house_x_mm / 2),
        cable_path_pan_w_mm,
        cable_path_h_mm + eps_mm
      ]);
    translate([m3_inset_mm, m3_inset_mm, 0])
      m3_through_hole(m3_boss_h_mm, m3_through_d_mm, eps_mm, quality_fn);
    translate([plate_mm - m3_inset_mm, m3_inset_mm, 0])
      m3_through_hole(m3_boss_h_mm, m3_through_d_mm, eps_mm, quality_fn);
    translate([m3_inset_mm, plate_mm - m3_inset_mm, 0])
      m3_through_hole(m3_boss_h_mm, m3_through_d_mm, eps_mm, quality_fn);
    translate([plate_mm - m3_inset_mm, plate_mm - m3_inset_mm, 0])
      m3_through_hole(m3_boss_h_mm, m3_through_d_mm, eps_mm, quality_fn);
    translate([mcu_origin_x + m2_boss_od_mm / 2, mcu_origin_y - m2_boss_od_mm / 2, 0])
      m2_through_hole(m2_boss_h_mm, m2_through_d_mm, eps_mm, quality_fn);
    translate([mcu_origin_x + mcu_pocket_l_mm - m2_boss_od_mm / 2, mcu_origin_y - m2_boss_od_mm / 2, 0])
      m2_through_hole(m2_boss_h_mm, m2_through_d_mm, eps_mm, quality_fn);
    translate([mcu_origin_x + m2_boss_od_mm / 2, mcu_origin_y + mcu_pocket_w_mm + m2_boss_od_mm / 2, 0])
      m2_through_hole(m2_boss_h_mm, m2_through_d_mm, eps_mm, quality_fn);
    translate([mcu_origin_x + mcu_pocket_l_mm - m2_boss_od_mm / 2, mcu_origin_y + mcu_pocket_w_mm + m2_boss_od_mm / 2, 0])
      m2_through_hole(m2_boss_h_mm, m2_through_d_mm, eps_mm, quality_fn);
    translate([plate_mm / 2, number_size_mm + 4, deck_thickness_mm - number_depth_mm])
      number_stamp("03");
  }
}

module yoke() {
  difference() {
    translate([-servo_house_x_mm / 2, -servo_house_y_mm / 2, 0])
      cube([servo_house_x_mm, servo_house_y_mm, servo_house_h_mm]);
    translate([0, 0, deck_thickness_mm])
      sg90_pocket_void(
        sg90_body_x_mm, sg90_body_y_mm, sg90_body_z_mm,
        sg90_tab_span_mm, sg90_tab_thick_mm, sg90_tab_width_mm,
        sg90_pocket_clearance_mm, eps_mm
      );
    translate([0, 0, deck_thickness_mm + sg90_body_z_mm])
      sg90_horn_clearance_void(sg90_horn_radius_mm, sg90_horn_clearance_h_mm, quality_fn, eps_mm);
    m2_through_hole(deck_thickness_mm, horn_id_mm, eps_mm, quality_fn);
    translate([
      -cable_path_tilt_w_mm / 2,
      servo_house_y_mm / 2 - wall_mm,
      deck_thickness_mm - cable_path_h_mm
    ])
      cube([cable_path_tilt_w_mm, wall_mm + eps_mm, cable_path_h_mm + eps_mm]);
  }
}

module stick() {
  difference() {
    union() {
      cylinder(d=horn_boss_od_mm, h=horn_pad_h_mm, $fn=quality_fn);
      translate([0, 0, horn_pad_h_mm])
        cylinder(d1=stick_base_d_mm, d2=stick_tip_d_mm, h=stick_h_mm, $fn=quality_fn);
    }
    m2_through_hole(horn_pad_h_mm + 6.0, horn_id_mm, eps_mm, quality_fn);
  }
}

module knob() {
  difference() {
    translate([0, 0, knob_d_mm / 2 - knob_flat_mm])
      sphere(d=knob_d_mm, $fn=quality_fn);
    translate([-knob_d_mm, -knob_d_mm, -knob_d_mm])
      cube([2 * knob_d_mm, 2 * knob_d_mm, knob_d_mm]);
    translate([0, 0, -eps_mm])
      cylinder(d=stick_tip_d_mm + 0.4, h=knob_d_mm, $fn=quality_fn);
  }
}

module bought_mcu() {
  translate([
    mcu_origin_x + mcu_pocket_clearance_mm,
    mcu_origin_y + mcu_pocket_clearance_mm,
    deck_thickness_mm - mcu_pocket_depth_mm
  ])
    cube([mcu_length_mm, mcu_width_mm, mcu_thickness_mm]);
}

module bought_sg90() {
  translate([-sg90_body_x_mm / 2, -sg90_body_y_mm / 2, 0])
    cube([sg90_body_x_mm, sg90_body_y_mm, sg90_body_z_mm]);
}

yoke_z = deck_thickness_mm + sg90_body_z_mm + 6.0;
stick_z = yoke_z + servo_house_h_mm + 4.0;

module gimbal_assembly() {
  color("#2B2B2B") base();
  color("#1B5E20") bought_mcu();
  color("#9E9E9E")
    translate([pan_center_x, pan_center_y, deck_thickness_mm])
      bought_sg90();
  color("#2B2B2B")
    translate([pan_center_x, pan_center_y, yoke_z])
      yoke();
  color("#9E9E9E")
    translate([pan_center_x, pan_center_y, yoke_z + deck_thickness_mm])
      bought_sg90();
  color("#D7CCC8")
    translate([pan_center_x, pan_center_y, stick_z])
      stick();
  color("#C62828")
    translate([
      pan_center_x,
      pan_center_y,
      stick_z + horn_pad_h_mm + stick_h_mm - (knob_d_mm / 2 - knob_flat_mm)
    ])
      knob();
}

module assembly() {
  gimbal_assembly();
}

if (which == "base") base();
else if (which == "yoke") yoke();
else if (which == "stick") stick();
else if (which == "knob") knob();
else if (which == "assembly") assembly();
