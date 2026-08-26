// Two-piece FDM display shell. Face-on-bed bezel, walls-up base. mm.

pcb_x = 88.3;
pcb_y = 64.3;
bezel_z = 2.4;
wall = 2.4;
floor_t = 2.4;
wall_h = 12;
window_inset = 5;
usb_w = 13.0;
usb_h = 8.5;
stemma_w = 22;
stemma_h = 9;
post_d = 6.5;
post_hole_d = 3.4;
post_inset = 6;
fit_clearance = 0.4;  // per side, bezel stop vs base cavity
which = "base";
$fn = 28;

outer_x = pcb_x + 2 * wall;
outer_y = pcb_y + 2 * wall;

module rounded_rect(x, y, r) {
    offset(r = r)
        offset(delta = -r)
            square([x, y], center = false);
}

module base() {
    difference() {
        union() {
            linear_extrude(height = floor_t)
                rounded_rect(outer_x, outer_y, 3);
            linear_extrude(height = floor_t + wall_h)
                difference() {
                    rounded_rect(outer_x, outer_y, 3);
                    translate([wall, wall])
                        square([pcb_x, pcb_y]);
                }
            for (sx = [post_inset, outer_x - post_inset],
                 sy = [post_inset, outer_y - post_inset])
                translate([sx, sy, 0])
                    cylinder(d = post_d, h = floor_t + 6);
        }
        // USB on the short edge (Y = 0)
        translate([outer_x / 2 - usb_w / 2, -1, floor_t + 2])
            cube([usb_w, wall + 2, usb_h]);
        // STEMMA on the opposite short edge
        translate([outer_x / 2 - stemma_w / 2, outer_y - wall - 1, floor_t + 2])
            cube([stemma_w, wall + 2, stemma_h]);
        for (sx = [post_inset, outer_x - post_inset],
             sy = [post_inset, outer_y - post_inset])
            translate([sx, sy, -1])
                cylinder(d = post_hole_d, h = floor_t + 10);
    }
}

module bezel() {
    stop = 1.2;
    stop_x = pcb_x - 2 * fit_clearance;
    stop_y = pcb_y - 2 * fit_clearance;
    difference() {
        union() {
            linear_extrude(height = bezel_z)
                rounded_rect(outer_x, outer_y, 3);
            translate([wall + fit_clearance, wall + fit_clearance, bezel_z])
                linear_extrude(height = stop)
                    difference() {
                        square([stop_x, stop_y]);
                        translate([1.2, 1.2])
                            square([stop_x - 2.4, stop_y - 2.4]);
                    }
        }
        translate([wall + window_inset, wall + window_inset, -1])
            cube([
                pcb_x - 2 * window_inset,
                pcb_y - 2 * window_inset,
                bezel_z + stop + 2
            ]);
        // reset poke
        translate([outer_x - 10, 10, -1])
            cylinder(d = 6.5, h = bezel_z + 2);
    }
}

if (which == "base") base();
else bezel();
