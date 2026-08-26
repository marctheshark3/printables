// MCU-pocket fit coupon — millimetres. Datasheet Super Mini class envelope.
mcu_length_mm = 22.5;
mcu_width_mm = 18.0;
mcu_pocket_clearance_mm = 0.4;
coupon_wall_mm = 2.4;
coupon_z_mm = 3.2;

difference() {
  cube([
    mcu_length_mm + 2 * mcu_pocket_clearance_mm + 2 * coupon_wall_mm,
    mcu_width_mm + 2 * mcu_pocket_clearance_mm + 2 * coupon_wall_mm,
    coupon_z_mm
  ]);
  translate([coupon_wall_mm, coupon_wall_mm, coupon_z_mm / 2])
    cube([
      mcu_length_mm + 2 * mcu_pocket_clearance_mm,
      mcu_width_mm + 2 * mcu_pocket_clearance_mm,
      coupon_z_mm
    ]);
}
