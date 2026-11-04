// CI specimen with an accessible underside for support-interface trials.
span_mm = 24;
width_mm = 12;
height_mm = 14;
wall_mm = 3;
union() {
    cube([wall_mm, width_mm, height_mm]);
    translate([span_mm-wall_mm, 0, 0]) cube([wall_mm, width_mm, height_mm]);
    translate([0, 0, height_mm-wall_mm]) cube([span_mm, width_mm, wall_mm]);
}
