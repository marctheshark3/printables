// Printable L-bracket coupon. L-profile in XY, extruded in Z (bed = XY).
// Units: millimetres.

object_x = 40;
object_y = 30;
object_z = 12;
flange = 12;
hole_d = 4.2;
hole_inset = 7;
$fn = 32;

module l_2d() {
    offset(r = 1.2)
        offset(delta = -1.2)
            union() {
                square([object_x, flange]);
                square([flange, object_y]);
            }
}

module holes_2d() {
    translate([14, flange / 2])
        circle(d = hole_d);
    translate([object_x - hole_inset, flange / 2])
        circle(d = hole_d);
    translate([flange / 2, object_y - hole_inset])
        circle(d = hole_d);
}

linear_extrude(height = object_z, convexity = 4)
    difference() {
        l_2d();
        holes_2d();
    }
