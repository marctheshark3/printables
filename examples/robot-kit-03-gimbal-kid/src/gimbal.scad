// robot-kit-03-gimbal — kid hull. Enclosed joystick, pan/tilt hidden, red knob.
// Millimetres. Export -D which="hull"|"lid"|"stick"|"knob".
// Preview-only: -D which="assembly".
// Yoke lives inside the hull as the stick's lower house. Not a stack of cubes.
use <lib/robot_kit.scad>

which = "hull";

/* [Hull] */
gim_hull_l_mm = 72.0;
gim_hull_w_mm = 72.0;
gim_hull_h_mm = 30.0;
gim_hull_r_mm = 14.0;
deck_thickness_mm = 3.2;
wall_mm = 2.4;
plate_mm = 72.0;

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

/* [Stick / knob / collar] */
stick_h_mm = 36.0;
stick_base_d_mm = 8.0;
stick_tip_d_mm = 4.0;
knob_d_mm = 16.0;
knob_flat_mm = 3.2;
horn_boss_od_mm = 10.0;
horn_id_mm = 2.4;
horn_pad_h_mm = 3.2;
collar_id_mm = 12.0;
collar_od_mm = 16.0;
collar_h_mm = 6.0;
yoke_w_mm = 28.0;
yoke_l_mm = 36.0;
yoke_h_mm = 22.0;
yoke_radius_mm = 6.0;

/* [Lid] */
gim_lid_t_mm = 3.2;
gim_lid_gap_mm = 0.4;

/* [M2/M3 ISO 273 medium — datasheet] */
m2_through_d_mm = 2.4;
m3_through_d_mm = 3.4;
m2_boss_od_mm = 5.6;
m3_boss_od_mm = 6.6;
m2_boss_h_mm = 4.0;
m3_boss_h_mm = 6.0;
gim_m3_inset_mm = 14.0;

/* [Bought envelopes — not printed] */
battery_envelope_h_mm = 6.0;

/* [Cable-path keepouts] */
cable_path_pan_w_mm = 4.0;
cable_path_tilt_w_mm = 4.0;
cable_path_h_mm = 1.6;

/* [Number stamp] */
gim_number_size_mm = 12.0;
gim_number_depth_mm = 0.8;

/* [Quality] */
quality_fn = 48;
eps_mm = 0.02;

gim_mcu_pocket_l_mm = mcu_length_mm + 2 * mcu_pocket_clearance_mm;
gim_mcu_pocket_w_mm = mcu_width_mm + 2 * mcu_pocket_clearance_mm;
gim_mcu_ox = wall_mm + m2_boss_od_mm;
gim_mcu_oy = wall_mm + m2_boss_od_mm;
gim_mcu_cy = gim_mcu_oy + gim_mcu_pocket_w_mm / 2;

gim_house_x_mm = sg90_tab_span_mm + 2 * sg90_pocket_clearance_mm + 2 * wall_mm;
gim_house_y_mm = sg90_body_y_mm + 2 * sg90_pocket_clearance_mm + 2 * wall_mm;
gim_house_h_mm = deck_thickness_mm + sg90_body_z_mm;
gim_pan_cx = gim_hull_l_mm / 2;
gim_pan_cy = gim_hull_w_mm / 2;
gim_inner_r_mm = gim_hull_r_mm - wall_mm;
gim_lid_z = gim_hull_h_mm + gim_lid_gap_mm;
gim_stick_z = deck_thickness_mm + sg90_body_z_mm + 2.4;

module gim_number_stamp(txt) {
  linear_extrude(height=gim_number_depth_mm + eps_mm)
    text(txt, size=gim_number_size_mm, font="Liberation Sans:style=Bold",
         halign="center", valign="center", $fn=quality_fn);
}

module gim_rounded_profile(l, w, r) {
  rr = min(r, l / 2 - 0.01, w / 2 - 0.01);
  translate([rr, rr])
    offset(r=rr)
      square([l - 2 * rr, w - 2 * rr]);
}

module gim_rounded_prism(l, w, h, r) {
  linear_extrude(height=h)
    gim_rounded_profile(l, w, r);
}

module gim_hull() {
  difference() {
    union() {
      gim_rounded_prism(gim_hull_l_mm, gim_hull_w_mm, deck_thickness_mm, gim_hull_r_mm);
      difference() {
        gim_rounded_prism(gim_hull_l_mm, gim_hull_w_mm, gim_hull_h_mm, gim_hull_r_mm);
        translate([wall_mm, wall_mm, -eps_mm])
          gim_rounded_prism(
            gim_hull_l_mm - 2 * wall_mm,
            gim_hull_w_mm - 2 * wall_mm,
            gim_hull_h_mm + 2 * eps_mm,
            gim_inner_r_mm
          );
      }
      translate([gim_m3_inset_mm, gim_m3_inset_mm, 0])
        cylinder(d=m3_boss_od_mm, h=gim_hull_h_mm, $fn=quality_fn);
      translate([gim_hull_l_mm - gim_m3_inset_mm, gim_m3_inset_mm, 0])
        cylinder(d=m3_boss_od_mm, h=gim_hull_h_mm, $fn=quality_fn);
      translate([gim_m3_inset_mm, gim_hull_w_mm - gim_m3_inset_mm, 0])
        cylinder(d=m3_boss_od_mm, h=gim_hull_h_mm, $fn=quality_fn);
      translate([gim_hull_l_mm - gim_m3_inset_mm, gim_hull_w_mm - gim_m3_inset_mm, 0])
        cylinder(d=m3_boss_od_mm, h=gim_hull_h_mm, $fn=quality_fn);
      translate([gim_mcu_ox + m2_boss_od_mm / 2, gim_mcu_oy - m2_boss_od_mm / 2, 0])
        cylinder(d=m2_boss_od_mm, h=m2_boss_h_mm, $fn=quality_fn);
      translate([gim_mcu_ox + gim_mcu_pocket_l_mm - m2_boss_od_mm / 2, gim_mcu_oy - m2_boss_od_mm / 2, 0])
        cylinder(d=m2_boss_od_mm, h=m2_boss_h_mm, $fn=quality_fn);
      translate([gim_mcu_ox + m2_boss_od_mm / 2, gim_mcu_oy + gim_mcu_pocket_w_mm + m2_boss_od_mm / 2, 0])
        cylinder(d=m2_boss_od_mm, h=m2_boss_h_mm, $fn=quality_fn);
      translate([gim_mcu_ox + gim_mcu_pocket_l_mm - m2_boss_od_mm / 2, gim_mcu_oy + gim_mcu_pocket_w_mm + m2_boss_od_mm / 2, 0])
        cylinder(d=m2_boss_od_mm, h=m2_boss_h_mm, $fn=quality_fn);
    }
    translate([gim_mcu_ox, gim_mcu_oy, deck_thickness_mm - mcu_pocket_depth_mm])
      mcu_pocket_void(
        mcu_length_mm, mcu_width_mm, mcu_pocket_depth_mm + mcu_thickness_mm,
        mcu_pocket_clearance_mm, eps_mm
      );
    translate([-eps_mm, gim_mcu_cy - usb_c_keepout_w_mm / 2, deck_thickness_mm - mcu_pocket_depth_mm])
      cube([usb_c_keepout_d_mm + eps_mm, usb_c_keepout_w_mm, usb_c_keepout_h_mm]);
    translate([gim_pan_cx, gim_pan_cy, deck_thickness_mm])
      sg90_pocket_void(
        sg90_body_x_mm, sg90_body_y_mm, sg90_body_z_mm,
        sg90_tab_span_mm, sg90_tab_thick_mm, sg90_tab_width_mm,
        sg90_pocket_clearance_mm, eps_mm
      );
    translate([gim_pan_cx, gim_pan_cy, deck_thickness_mm + sg90_body_z_mm])
      sg90_horn_clearance_void(sg90_horn_radius_mm, sg90_horn_clearance_h_mm, quality_fn, eps_mm);
    translate([
      gim_mcu_ox + gim_mcu_pocket_l_mm,
      gim_mcu_cy - cable_path_pan_w_mm / 2,
      deck_thickness_mm - cable_path_h_mm
    ])
      cube([
        gim_pan_cx - (gim_mcu_ox + gim_mcu_pocket_l_mm),
        cable_path_pan_w_mm,
        cable_path_h_mm + eps_mm
      ]);
    translate([gim_m3_inset_mm, gim_m3_inset_mm, 0])
      m3_through_hole(gim_hull_h_mm, m3_through_d_mm, eps_mm, quality_fn);
    translate([gim_hull_l_mm - gim_m3_inset_mm, gim_m3_inset_mm, 0])
      m3_through_hole(gim_hull_h_mm, m3_through_d_mm, eps_mm, quality_fn);
    translate([gim_m3_inset_mm, gim_hull_w_mm - gim_m3_inset_mm, 0])
      m3_through_hole(gim_hull_h_mm, m3_through_d_mm, eps_mm, quality_fn);
    translate([gim_hull_l_mm - gim_m3_inset_mm, gim_hull_w_mm - gim_m3_inset_mm, 0])
      m3_through_hole(gim_hull_h_mm, m3_through_d_mm, eps_mm, quality_fn);
    translate([gim_mcu_ox + m2_boss_od_mm / 2, gim_mcu_oy - m2_boss_od_mm / 2, 0])
      m2_through_hole(m2_boss_h_mm, m2_through_d_mm, eps_mm, quality_fn);
    translate([gim_mcu_ox + gim_mcu_pocket_l_mm - m2_boss_od_mm / 2, gim_mcu_oy - m2_boss_od_mm / 2, 0])
      m2_through_hole(m2_boss_h_mm, m2_through_d_mm, eps_mm, quality_fn);
    translate([gim_mcu_ox + m2_boss_od_mm / 2, gim_mcu_oy + gim_mcu_pocket_w_mm + m2_boss_od_mm / 2, 0])
      m2_through_hole(m2_boss_h_mm, m2_through_d_mm, eps_mm, quality_fn);
    translate([gim_mcu_ox + gim_mcu_pocket_l_mm - m2_boss_od_mm / 2, gim_mcu_oy + gim_mcu_pocket_w_mm + m2_boss_od_mm / 2, 0])
      m2_through_hole(m2_boss_h_mm, m2_through_d_mm, eps_mm, quality_fn);
    translate([gim_hull_l_mm - gim_number_depth_mm, gim_hull_w_mm / 2, gim_hull_h_mm * 0.52])
      rotate([90, 0, 90])
        gim_number_stamp("03");
  }
}

module gim_lid() {
  difference() {
    union() {
      gim_rounded_prism(gim_hull_l_mm, gim_hull_w_mm, gim_lid_t_mm, gim_hull_r_mm);
      translate([gim_pan_cx, gim_pan_cy, 0])
        cylinder(d=collar_od_mm, h=gim_lid_t_mm + collar_h_mm, $fn=quality_fn);
    }
    translate([gim_pan_cx, gim_pan_cy, -eps_mm])
      cylinder(d=collar_id_mm, h=gim_lid_t_mm + collar_h_mm + 2 * eps_mm, $fn=quality_fn);
    translate([gim_m3_inset_mm, gim_m3_inset_mm, 0])
      m3_through_hole(gim_lid_t_mm, m3_through_d_mm, eps_mm, quality_fn);
    translate([gim_hull_l_mm - gim_m3_inset_mm, gim_m3_inset_mm, 0])
      m3_through_hole(gim_lid_t_mm, m3_through_d_mm, eps_mm, quality_fn);
    translate([gim_m3_inset_mm, gim_hull_w_mm - gim_m3_inset_mm, 0])
      m3_through_hole(gim_lid_t_mm, m3_through_d_mm, eps_mm, quality_fn);
    translate([gim_hull_l_mm - gim_m3_inset_mm, gim_hull_w_mm - gim_m3_inset_mm, 0])
      m3_through_hole(gim_lid_t_mm, m3_through_d_mm, eps_mm, quality_fn);
  }
}

module gim_stick() {
  // Shaft through the lid collar. Tilt yoke lives inside the hull, not exported.
  difference() {
    union() {
      cylinder(d=horn_boss_od_mm, h=horn_pad_h_mm, $fn=quality_fn);
      translate([0, 0, horn_pad_h_mm])
        cylinder(d1=stick_base_d_mm, d2=stick_tip_d_mm, h=stick_h_mm, $fn=quality_fn);
    }
    m2_through_hole(horn_pad_h_mm + 6.0, horn_id_mm, eps_mm, quality_fn);
  }
}

module gim_knob() {
  difference() {
    translate([0, 0, knob_d_mm / 2 - knob_flat_mm])
      sphere(d=knob_d_mm, $fn=quality_fn);
    translate([-knob_d_mm, -knob_d_mm, -knob_d_mm])
      cube([2 * knob_d_mm, 2 * knob_d_mm, knob_d_mm]);
    translate([0, 0, -eps_mm])
      cylinder(d=stick_tip_d_mm + 0.4, h=knob_d_mm, $fn=quality_fn);
  }
}

module gim_bought_mcu() {
  translate([
    gim_mcu_ox + mcu_pocket_clearance_mm,
    gim_mcu_oy + mcu_pocket_clearance_mm,
    deck_thickness_mm - mcu_pocket_depth_mm
  ])
    cube([mcu_length_mm, mcu_width_mm, mcu_thickness_mm]);
}

module gim_bought_sg90() {
  translate([-sg90_body_x_mm / 2, -sg90_body_y_mm / 2, 0])
    cube([sg90_body_x_mm, sg90_body_y_mm, sg90_body_z_mm]);
}

module gim_ground() {
  translate([-20, -20, -0.8])
    cube([gim_hull_l_mm + 40, gim_hull_w_mm + 40, 0.8]);
}

module gimbal_assembly() {
  color("#1C1C1C") gim_hull();
  color("#1C1C1C")
    translate([0, 0, gim_lid_z])
      gim_lid();
  color("#D7CCC8")
    translate([gim_pan_cx, gim_pan_cy, gim_stick_z])
      gim_stick();
  color("#C62828")
    translate([
      gim_pan_cx,
      gim_pan_cy,
      gim_stick_z + horn_pad_h_mm + stick_h_mm - (knob_d_mm / 2 - knob_flat_mm)
    ])
      gim_knob();
  color("#1B5E20") gim_bought_mcu();
  color("#9E9E9E")
    translate([gim_pan_cx, gim_pan_cy, deck_thickness_mm])
      gim_bought_sg90();
  color("#C8C0B4") gim_ground();
}

module assembly() {
  gimbal_assembly();
}

if (which == "hull") gim_hull();
else if (which == "lid") gim_lid();
else if (which == "stick") gim_stick();
else if (which == "knob") gim_knob();
else if (which == "assembly") assembly();
