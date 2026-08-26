// robot-kit-02-gripper — numbered 02 servo gripper arm.
// Millimetres. Export -D which="base"|"link"|"wrist"|"finger".
// Preview-only: -D which="assembly".
// SG90/9g at the base; distal links are SHORT blocky horn plates (8 mm),
// not a 9g SCARA tower. Gold library has SG90 only — wrist uses the same
// pocket family. Red printed fingers. MCU on deck.
use <lib/robot_kit.scad>

which = "base";

/* [Base] */
base_length_mm = 70.0;
base_width_mm = 40.0;
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

/* [SG90 / 9g micro servo — datasheet class, same as gold v2] */
sg90_body_x_mm = 22.8;
sg90_body_y_mm = 12.2;
sg90_body_z_mm = 22.8;
sg90_tab_span_mm = 32.3;
sg90_tab_thick_mm = 2.5;
sg90_tab_width_mm = 12.0;
sg90_pocket_clearance_mm = 0.4;
sg90_horn_radius_mm = 16.0;
sg90_horn_clearance_h_mm = 6.0;

/* [Short blocky distal link — not a 9g wrap; 8 mm vs old 14.7] */
link_length_mm = 26.0;
link_width_mm = 16.0;
link_thickness_mm = 8.0;
horn_boss_od_mm = 10.0;
horn_id_mm = 2.4;
horn_span_mm = 18.0;

/* [Finger] */
finger_length_mm = 22.0;
finger_height_mm = 8.0;
finger_thick_mm = 3.2;
finger_tip_drop_mm = 8.0;

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
cable_path_servo_base_w_mm = 4.0;
cable_path_servo_grip_w_mm = 4.0;
cable_path_h_mm = 1.6;

/* [Number stamp] */
number_size_mm = 9.0;
number_depth_mm = 0.8;

/* [Quality] */
quality_fn = 48;
eps_mm = 0.02;

mcu_pocket_l_mm = mcu_length_mm + 2 * mcu_pocket_clearance_mm;
mcu_pocket_w_mm = mcu_width_mm + 2 * mcu_pocket_clearance_mm;
mcu_origin_x = wall_mm + m2_boss_od_mm;
mcu_origin_y = (base_width_mm - mcu_pocket_w_mm) / 2;
mcu_center_y = base_width_mm / 2;

servo_house_x_mm = sg90_tab_span_mm + 2 * sg90_pocket_clearance_mm + 2 * wall_mm;
servo_house_y_mm = sg90_body_y_mm + 2 * sg90_pocket_clearance_mm + 2 * wall_mm;
servo_house_h_mm = deck_thickness_mm + sg90_body_z_mm + 2 * sg90_pocket_clearance_mm;
servo_center_x = base_length_mm - wall_mm - sg90_tab_span_mm / 2;
servo_center_y = mcu_center_y;

module number_stamp(txt) {
  linear_extrude(height=number_depth_mm + eps_mm)
    text(txt, size=number_size_mm, font="Liberation Sans:style=Bold",
         halign="center", valign="center", $fn=quality_fn);
}

module sg90_house_solid() {
  translate([-servo_house_x_mm / 2, -servo_house_y_mm / 2, 0])
    cube([servo_house_x_mm, servo_house_y_mm, servo_house_h_mm]);
}

module base() {
  difference() {
    union() {
      cube([base_length_mm, base_width_mm, deck_thickness_mm]);
      cube([wall_mm, base_width_mm, deck_thickness_mm + usb_c_keepout_h_mm]);
      translate([servo_center_x, servo_center_y, 0])
        sg90_house_solid();
      translate([m3_inset_mm, m3_inset_mm, 0])
        cylinder(d=m3_boss_od_mm, h=m3_boss_h_mm, $fn=quality_fn);
      translate([base_length_mm - m3_inset_mm, m3_inset_mm, 0])
        cylinder(d=m3_boss_od_mm, h=m3_boss_h_mm, $fn=quality_fn);
      translate([m3_inset_mm, base_width_mm - m3_inset_mm, 0])
        cylinder(d=m3_boss_od_mm, h=m3_boss_h_mm, $fn=quality_fn);
      translate([base_length_mm - m3_inset_mm, base_width_mm - m3_inset_mm, 0])
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
    translate([servo_center_x, servo_center_y, deck_thickness_mm])
      sg90_pocket_void(
        sg90_body_x_mm, sg90_body_y_mm, sg90_body_z_mm,
        sg90_tab_span_mm, sg90_tab_thick_mm, sg90_tab_width_mm,
        sg90_pocket_clearance_mm, eps_mm
      );
    translate([servo_center_x, servo_center_y, deck_thickness_mm + sg90_body_z_mm])
      sg90_horn_clearance_void(sg90_horn_radius_mm, sg90_horn_clearance_h_mm, quality_fn, eps_mm);
    translate([
      mcu_origin_x + mcu_pocket_l_mm,
      mcu_center_y - cable_path_servo_base_w_mm / 2,
      deck_thickness_mm - cable_path_h_mm
    ])
      cube([
        servo_center_x - (mcu_origin_x + mcu_pocket_l_mm),
        cable_path_servo_base_w_mm,
        cable_path_h_mm + eps_mm
      ]);
    translate([m3_inset_mm, m3_inset_mm, 0])
      m3_through_hole(m3_boss_h_mm, m3_through_d_mm, eps_mm, quality_fn);
    translate([base_length_mm - m3_inset_mm, m3_inset_mm, 0])
      m3_through_hole(m3_boss_h_mm, m3_through_d_mm, eps_mm, quality_fn);
    translate([m3_inset_mm, base_width_mm - m3_inset_mm, 0])
      m3_through_hole(m3_boss_h_mm, m3_through_d_mm, eps_mm, quality_fn);
    translate([base_length_mm - m3_inset_mm, base_width_mm - m3_inset_mm, 0])
      m3_through_hole(m3_boss_h_mm, m3_through_d_mm, eps_mm, quality_fn);
    translate([mcu_origin_x + m2_boss_od_mm / 2, mcu_origin_y - m2_boss_od_mm / 2, 0])
      m2_through_hole(m2_boss_h_mm, m2_through_d_mm, eps_mm, quality_fn);
    translate([mcu_origin_x + mcu_pocket_l_mm - m2_boss_od_mm / 2, mcu_origin_y - m2_boss_od_mm / 2, 0])
      m2_through_hole(m2_boss_h_mm, m2_through_d_mm, eps_mm, quality_fn);
    translate([mcu_origin_x + m2_boss_od_mm / 2, mcu_origin_y + mcu_pocket_w_mm + m2_boss_od_mm / 2, 0])
      m2_through_hole(m2_boss_h_mm, m2_through_d_mm, eps_mm, quality_fn);
    translate([mcu_origin_x + mcu_pocket_l_mm - m2_boss_od_mm / 2, mcu_origin_y + mcu_pocket_w_mm + m2_boss_od_mm / 2, 0])
      m2_through_hole(m2_boss_h_mm, m2_through_d_mm, eps_mm, quality_fn);
    translate([base_length_mm - number_depth_mm, servo_center_y, servo_house_h_mm * 0.55])
      rotate([90, 0, 90])
        number_stamp("02");
    translate([servo_center_x, number_depth_mm, servo_house_h_mm * 0.55])
      rotate([90, 0, 0])
        number_stamp("02");
  }
}

module link() {
  difference() {
    hull() {
      translate([0, 0, 0])
        cylinder(d=link_width_mm, h=link_thickness_mm, $fn=quality_fn);
      translate([horn_span_mm, 0, 0])
        cylinder(d=link_width_mm, h=link_thickness_mm, $fn=quality_fn);
    }
    m2_through_hole(link_thickness_mm, horn_id_mm, eps_mm, quality_fn);
    translate([horn_span_mm, 0, 0])
      m2_through_hole(link_thickness_mm, horn_id_mm, eps_mm, quality_fn);
  }
}

module wrist() {
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
    translate([0, -servo_house_y_mm / 2, servo_house_h_mm / 2])
      rotate([90, 0, 0])
        through_hole(horn_id_mm, wall_mm, eps_mm, quality_fn);
    translate([
      -cable_path_servo_grip_w_mm / 2,
      servo_house_y_mm / 2 - wall_mm,
      deck_thickness_mm - cable_path_h_mm
    ])
      cube([
        cable_path_servo_grip_w_mm,
        wall_mm + eps_mm,
        cable_path_h_mm + eps_mm
      ]);
  }
}

module finger() {
  difference() {
    union() {
      hull() {
        cylinder(d=finger_height_mm, h=finger_thick_mm, $fn=quality_fn);
        translate([finger_length_mm * 0.55, 1.6, 0])
          cylinder(d=finger_height_mm * 0.75, h=finger_thick_mm, $fn=quality_fn);
      }
      hull() {
        translate([finger_length_mm * 0.55, 1.6, 0])
          cylinder(d=finger_height_mm * 0.75, h=finger_thick_mm, $fn=quality_fn);
        translate([finger_length_mm, finger_tip_drop_mm, 0])
          cylinder(d=4.0, h=finger_thick_mm, $fn=quality_fn);
      }
    }
    m2_through_hole(finger_thick_mm, horn_id_mm, eps_mm, quality_fn);
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

horn_z = deck_thickness_mm + sg90_body_z_mm + 2.0;
link_lift = horn_z + 1.0;
wrist_z = link_lift + link_thickness_mm + 2.0;
finger_z = wrist_z + servo_house_h_mm + 4.0;

module gripper_assembly() {
  color("#2B2B2B") base();
  color("#1B5E20") bought_mcu();
  color("#9E9E9E")
    translate([servo_center_x, servo_center_y, deck_thickness_mm])
      bought_sg90();
  color("#2B2B2B")
    translate([servo_center_x, servo_center_y, link_lift])
      link();
  color("#2B2B2B")
    translate([servo_center_x, servo_center_y, wrist_z])
      wrist();
  color("#9E9E9E")
    translate([servo_center_x, servo_center_y, wrist_z + deck_thickness_mm])
      bought_sg90();
  color("#C62828") {
    translate([servo_center_x, servo_center_y - 12, finger_z])
      finger();
    translate([servo_center_x, servo_center_y + 12, finger_z])
      finger();
  }
}

module assembly() {
  gripper_assembly();
}

if (which == "base") base();
else if (which == "link") link();
else if (which == "wrist") wrist();
else if (which == "finger") finger();
else if (which == "assembly") assembly();
