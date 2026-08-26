// robot-kit-02-gripper — kid claw-bot. Enclosed torso, sleeved forearm, pincers.
// Millimetres. Export -D which="hull"|"lid"|"sleeve"|"finger".
// Preview-only: -D which="assembly".
// Base SG90 in the torso pocket; wrist SG90 lives INSIDE the sleeve (styling).
// Distal 8 mm horn plate is inside the sleeve, not a naked brick.
use <lib/robot_kit.scad>

which = "hull";

/* [Torso hull] */
hull_length_mm = 70.0;
hull_width_mm = 48.0;
hull_h_mm = 28.0;
hull_radius_mm = 12.0;
deck_thickness_mm = 3.2;
wall_mm = 2.4;
base_length_mm = 70.0;
base_width_mm = 48.0;

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

/* [Short 8 mm horn plate — lives INSIDE the sleeve] */
link_length_mm = 26.0;
link_width_mm = 16.0;
link_thickness_mm = 8.0;
horn_boss_od_mm = 10.0;
horn_id_mm = 2.4;
horn_span_mm = 18.0;
sleeve_neck_od_mm = 16.0;
sleeve_outer_w_mm = 22.0;
sleeve_outer_h_mm = 28.0;
sleeve_radius_mm = 10.0;

/* [Claw finger — curved pincer] */
finger_length_mm = 32.0;
finger_height_mm = 10.0;
finger_thick_mm = 6.0;
finger_tip_drop_mm = 10.0;
claw_open_deg = 22.0;
arm_elev_deg = -52.0;
arm_yaw_deg = 8.0;

/* [Lid] */
lid_thickness_mm = 3.2;
lid_clearance_mm = 0.4;
lid_window_l_mm = 16.0;
lid_window_w_mm = 11.0;
lid_horn_hole_d_mm = 22.0;

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
cable_path_servo_base_w_mm = 4.0;
cable_path_servo_grip_w_mm = 4.0;
cable_path_h_mm = 1.6;

/* [Number stamp] */
number_size_mm = 12.0;
number_depth_mm = 0.8;

/* [Quality] */
quality_fn = 48;
eps_mm = 0.02;

grip_mcu_pocket_l_mm = mcu_length_mm + 2 * mcu_pocket_clearance_mm;
grip_mcu_pocket_w_mm = mcu_width_mm + 2 * mcu_pocket_clearance_mm;
grip_mcu_ox = wall_mm + m2_boss_od_mm;
grip_mcu_oy = (hull_width_mm - grip_mcu_pocket_w_mm) / 2;
grip_mcu_cy = hull_width_mm / 2;

grip_house_x_mm = sg90_tab_span_mm + 2 * sg90_pocket_clearance_mm + 2 * wall_mm;
grip_house_y_mm = sg90_body_y_mm + 2 * sg90_pocket_clearance_mm + 2 * wall_mm;
grip_house_h_mm = deck_thickness_mm + sg90_body_z_mm;
grip_servo_cx = hull_length_mm - wall_mm - sg90_tab_span_mm / 2;
grip_servo_cy = hull_width_mm - wall_mm - grip_house_y_mm / 2;
grip_inner_r_mm = hull_radius_mm - wall_mm;
grip_lid_z = hull_h_mm + lid_clearance_mm;
grip_horn_z = grip_lid_z + lid_thickness_mm + 8.0;
grip_sleeve_len_mm = link_thickness_mm + wall_mm + sg90_body_x_mm + 10.0;

module grip_number_stamp(txt) {
  linear_extrude(height=number_depth_mm + eps_mm)
    text(txt, size=number_size_mm, font="Liberation Sans:style=Bold",
         halign="center", valign="center", $fn=quality_fn);
}

module grip_rounded_profile(l, w, r) {
  rr = min(r, l / 2 - 0.01, w / 2 - 0.01);
  translate([rr, rr])
    offset(r=rr)
      square([l - 2 * rr, w - 2 * rr]);
}

module grip_rounded_prism(l, w, h, r) {
  linear_extrude(height=h)
    grip_rounded_profile(l, w, r);
}

module grip_hull() {
  difference() {
    union() {
      grip_rounded_prism(hull_length_mm, hull_width_mm, deck_thickness_mm, hull_radius_mm);
      difference() {
        grip_rounded_prism(hull_length_mm, hull_width_mm, hull_h_mm, hull_radius_mm);
        translate([wall_mm, wall_mm, -eps_mm])
          grip_rounded_prism(
            hull_length_mm - 2 * wall_mm,
            hull_width_mm - 2 * wall_mm,
            hull_h_mm + 2 * eps_mm,
            grip_inner_r_mm
          );
      }
      // Shoulder fairing — rounded bump around the base SG90, part of hull.
      translate([
        grip_servo_cx - grip_house_x_mm / 2,
        grip_servo_cy - grip_house_y_mm / 2 - wall_mm,
        0
      ])
        grip_rounded_prism(
          grip_house_x_mm,
          grip_house_y_mm + 2 * wall_mm,
          hull_h_mm,
          6.0
        );
      translate([m3_inset_mm, m3_inset_mm, 0])
        cylinder(d=m3_boss_od_mm, h=hull_h_mm, $fn=quality_fn);
      translate([hull_length_mm - m3_inset_mm, m3_inset_mm, 0])
        cylinder(d=m3_boss_od_mm, h=hull_h_mm, $fn=quality_fn);
      translate([m3_inset_mm, hull_width_mm - m3_inset_mm, 0])
        cylinder(d=m3_boss_od_mm, h=hull_h_mm, $fn=quality_fn);
      translate([hull_length_mm - m3_inset_mm, hull_width_mm - m3_inset_mm, 0])
        cylinder(d=m3_boss_od_mm, h=hull_h_mm, $fn=quality_fn);
      translate([grip_mcu_ox + m2_boss_od_mm / 2, grip_mcu_oy - m2_boss_od_mm / 2, 0])
        cylinder(d=m2_boss_od_mm, h=m2_boss_h_mm, $fn=quality_fn);
      translate([grip_mcu_ox + grip_mcu_pocket_l_mm - m2_boss_od_mm / 2, grip_mcu_oy - m2_boss_od_mm / 2, 0])
        cylinder(d=m2_boss_od_mm, h=m2_boss_h_mm, $fn=quality_fn);
      translate([grip_mcu_ox + m2_boss_od_mm / 2, grip_mcu_oy + grip_mcu_pocket_w_mm + m2_boss_od_mm / 2, 0])
        cylinder(d=m2_boss_od_mm, h=m2_boss_h_mm, $fn=quality_fn);
      translate([grip_mcu_ox + grip_mcu_pocket_l_mm - m2_boss_od_mm / 2, grip_mcu_oy + grip_mcu_pocket_w_mm + m2_boss_od_mm / 2, 0])
        cylinder(d=m2_boss_od_mm, h=m2_boss_h_mm, $fn=quality_fn);
    }
    translate([grip_mcu_ox, grip_mcu_oy, deck_thickness_mm - mcu_pocket_depth_mm])
      mcu_pocket_void(
        mcu_length_mm, mcu_width_mm, mcu_pocket_depth_mm + mcu_thickness_mm,
        mcu_pocket_clearance_mm, eps_mm
      );
    translate([-eps_mm, grip_mcu_cy - usb_c_keepout_w_mm / 2, deck_thickness_mm - mcu_pocket_depth_mm])
      cube([usb_c_keepout_d_mm + eps_mm, usb_c_keepout_w_mm, usb_c_keepout_h_mm]);
    translate([grip_servo_cx, grip_servo_cy, deck_thickness_mm])
      sg90_pocket_void(
        sg90_body_x_mm, sg90_body_y_mm, sg90_body_z_mm,
        sg90_tab_span_mm, sg90_tab_thick_mm, sg90_tab_width_mm,
        sg90_pocket_clearance_mm, eps_mm
      );
    translate([grip_servo_cx, grip_servo_cy, deck_thickness_mm + sg90_body_z_mm])
      sg90_horn_clearance_void(sg90_horn_radius_mm, sg90_horn_clearance_h_mm, quality_fn, eps_mm);
    translate([
      grip_mcu_ox + grip_mcu_pocket_l_mm,
      grip_mcu_cy - cable_path_servo_base_w_mm / 2,
      deck_thickness_mm - cable_path_h_mm
    ])
      cube([
        grip_servo_cx - (grip_mcu_ox + grip_mcu_pocket_l_mm),
        cable_path_servo_base_w_mm,
        cable_path_h_mm + eps_mm
      ]);
    translate([m3_inset_mm, m3_inset_mm, 0])
      m3_through_hole(hull_h_mm, m3_through_d_mm, eps_mm, quality_fn);
    translate([hull_length_mm - m3_inset_mm, m3_inset_mm, 0])
      m3_through_hole(hull_h_mm, m3_through_d_mm, eps_mm, quality_fn);
    translate([m3_inset_mm, hull_width_mm - m3_inset_mm, 0])
      m3_through_hole(hull_h_mm, m3_through_d_mm, eps_mm, quality_fn);
    translate([hull_length_mm - m3_inset_mm, hull_width_mm - m3_inset_mm, 0])
      m3_through_hole(hull_h_mm, m3_through_d_mm, eps_mm, quality_fn);
    translate([grip_mcu_ox + m2_boss_od_mm / 2, grip_mcu_oy - m2_boss_od_mm / 2, 0])
      m2_through_hole(m2_boss_h_mm, m2_through_d_mm, eps_mm, quality_fn);
    translate([grip_mcu_ox + grip_mcu_pocket_l_mm - m2_boss_od_mm / 2, grip_mcu_oy - m2_boss_od_mm / 2, 0])
      m2_through_hole(m2_boss_h_mm, m2_through_d_mm, eps_mm, quality_fn);
    translate([grip_mcu_ox + m2_boss_od_mm / 2, grip_mcu_oy + grip_mcu_pocket_w_mm + m2_boss_od_mm / 2, 0])
      m2_through_hole(m2_boss_h_mm, m2_through_d_mm, eps_mm, quality_fn);
    translate([grip_mcu_ox + grip_mcu_pocket_l_mm - m2_boss_od_mm / 2, grip_mcu_oy + grip_mcu_pocket_w_mm + m2_boss_od_mm / 2, 0])
      m2_through_hole(m2_boss_h_mm, m2_through_d_mm, eps_mm, quality_fn);
    // 02 on the chest, big, readable.
    translate([hull_length_mm - number_depth_mm, grip_mcu_cy, hull_h_mm * 0.55])
      rotate([90, 0, 90])
        grip_number_stamp("02");
  }
}

module grip_lid() {
  difference() {
    union() {
      grip_rounded_prism(hull_length_mm, hull_width_mm, lid_thickness_mm, hull_radius_mm);
      // Shoulder collar around the horn.
      translate([grip_servo_cx, grip_servo_cy, 0])
        cylinder(d=sleeve_neck_od_mm + 2 * wall_mm, h=lid_thickness_mm + 8.0, $fn=quality_fn);
    }
    translate([
      grip_mcu_ox + grip_mcu_pocket_l_mm / 2,
      grip_mcu_cy,
      -eps_mm
    ])
      hull() {
        translate([-lid_window_l_mm / 2 + 2, 0, 0])
          cylinder(d=lid_window_w_mm, h=lid_thickness_mm + 2 * eps_mm, $fn=quality_fn);
        translate([lid_window_l_mm / 2 - 2, 0, 0])
          cylinder(d=lid_window_w_mm, h=lid_thickness_mm + 2 * eps_mm, $fn=quality_fn);
      }
    translate([grip_servo_cx, grip_servo_cy, -eps_mm])
      cylinder(d=lid_horn_hole_d_mm, h=lid_thickness_mm + 4.0, $fn=quality_fn);
    translate([m3_inset_mm, m3_inset_mm, 0])
      m3_through_hole(lid_thickness_mm, m3_through_d_mm, eps_mm, quality_fn);
    translate([hull_length_mm - m3_inset_mm, m3_inset_mm, 0])
      m3_through_hole(lid_thickness_mm, m3_through_d_mm, eps_mm, quality_fn);
    translate([m3_inset_mm, hull_width_mm - m3_inset_mm, 0])
      m3_through_hole(lid_thickness_mm, m3_through_d_mm, eps_mm, quality_fn);
    translate([hull_length_mm - m3_inset_mm, hull_width_mm - m3_inset_mm, 0])
      m3_through_hole(lid_thickness_mm, m3_through_d_mm, eps_mm, quality_fn);
  }
}

module grip_sleeve() {
  // Capsule forearm: 8 mm neck + sleeved SG90 house. Reads as an arm, not a brick.
  difference() {
    union() {
      cylinder(d=sleeve_neck_od_mm, h=link_thickness_mm, $fn=quality_fn);
      hull() {
        translate([2, 0, sleeve_outer_h_mm / 2])
          sphere(d=sleeve_outer_w_mm, $fn=quality_fn);
        translate([grip_sleeve_len_mm, 0, sleeve_outer_h_mm / 2])
          sphere(d=sleeve_outer_w_mm, $fn=quality_fn);
      }
    }
    m2_through_hole(link_thickness_mm, horn_id_mm, eps_mm, quality_fn);
    translate([
      link_thickness_mm + wall_mm + sg90_body_x_mm / 2,
      0,
      wall_mm
    ])
      sg90_pocket_void(
        sg90_body_x_mm, sg90_body_y_mm, sg90_body_z_mm,
        sg90_tab_span_mm, sg90_tab_thick_mm, sg90_tab_width_mm,
        sg90_pocket_clearance_mm, eps_mm
      );
    translate([
      link_thickness_mm + wall_mm + sg90_body_x_mm / 2,
      0,
      wall_mm + sg90_body_z_mm
    ])
      sg90_horn_clearance_void(6.0, 4.0, quality_fn, eps_mm);
    translate([
      link_thickness_mm,
      -cable_path_servo_grip_w_mm / 2,
      wall_mm
    ])
      cube([
        cable_path_servo_grip_w_mm,
        cable_path_servo_grip_w_mm,
        cable_path_h_mm + wall_mm
      ]);
    translate([grip_sleeve_len_mm - 6.0, sleeve_outer_w_mm / 2, sleeve_outer_h_mm / 2])
      rotate([90, 0, 0])
        through_hole(horn_id_mm, sleeve_outer_w_mm, eps_mm, quality_fn);
  }
}

module grip_finger() {
  // Curved crab/pincer — not an L-bracket.
  difference() {
    union() {
      cylinder(d=finger_height_mm, h=finger_thick_mm, $fn=quality_fn);
      hull() {
        cylinder(d=finger_height_mm, h=finger_thick_mm, $fn=quality_fn);
        translate([finger_length_mm * 0.42, 5.0, 0])
          cylinder(d=finger_height_mm * 0.85, h=finger_thick_mm, $fn=quality_fn);
      }
      hull() {
        translate([finger_length_mm * 0.42, 5.0, 0])
          cylinder(d=finger_height_mm * 0.85, h=finger_thick_mm, $fn=quality_fn);
        translate([finger_length_mm * 0.78, 9.5, 0])
          cylinder(d=finger_height_mm * 0.55, h=finger_thick_mm, $fn=quality_fn);
      }
      hull() {
        translate([finger_length_mm * 0.78, 9.5, 0])
          cylinder(d=finger_height_mm * 0.55, h=finger_thick_mm, $fn=quality_fn);
        translate([finger_length_mm, finger_tip_drop_mm * 0.45, 0])
          cylinder(d=3.6, h=finger_thick_mm, $fn=quality_fn);
      }
    }
    m2_through_hole(finger_thick_mm, horn_id_mm, eps_mm, quality_fn);
  }
}

module grip_bought_mcu() {
  translate([
    grip_mcu_ox + mcu_pocket_clearance_mm,
    grip_mcu_oy + mcu_pocket_clearance_mm,
    deck_thickness_mm - mcu_pocket_depth_mm
  ])
    cube([mcu_length_mm, mcu_width_mm, mcu_thickness_mm]);
}

module grip_bought_sg90() {
  translate([-sg90_body_x_mm / 2, -sg90_body_y_mm / 2, 0])
    cube([sg90_body_x_mm, sg90_body_y_mm, sg90_body_z_mm]);
}

module grip_ground() {
  translate([-24, -28, -0.8])
    cube([hull_length_mm + 90, hull_width_mm + 56, 0.8]);
}

module grip_placed_sleeve() {
  translate([grip_servo_cx, grip_servo_cy, grip_horn_z])
    rotate([0, arm_elev_deg, arm_yaw_deg])
      grip_sleeve();
}

module grip_placed_finger(side) {
  // side: -1 left, +1 right. Claws slightly open, meeting like a pincer.
  translate([grip_servo_cx, grip_servo_cy, grip_horn_z])
    rotate([0, arm_elev_deg, arm_yaw_deg])
      translate([
        grip_sleeve_len_mm + 1.2,
        side * 6.0,
        (sleeve_outer_h_mm - finger_thick_mm) / 2
      ])
        rotate([0, 0, side * claw_open_deg])
          mirror([0, side < 0 ? 1 : 0, 0])
            grip_finger();
}

module gripper_assembly() {
  color("#1C1C1C") grip_hull();
  color("#1C1C1C")
    translate([0, 0, grip_lid_z])
      grip_lid();
  color("#1C1C1C") grip_placed_sleeve();
  color("#C62828") {
    grip_placed_finger(-1);
    grip_placed_finger(1);
  }
  color("#1B5E20") grip_bought_mcu();
  color("#9E9E9E")
    translate([grip_servo_cx, grip_servo_cy, deck_thickness_mm])
      grip_bought_sg90();
  color("#C8C0B4") grip_ground();
}

module assembly() {
  gripper_assembly();
}

if (which == "hull") grip_hull();
else if (which == "lid") grip_lid();
else if (which == "sleeve") grip_sleeve();
else if (which == "finger") grip_finger();
else if (which == "assembly") assembly();
