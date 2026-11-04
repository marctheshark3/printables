// CI specimen: a pebble-shaped lid with an inlaid direction arrow.
// Invented dimensions; no mating fit or physical performance claim.
length_mm = 50;
width_mm = 34;
thickness_mm = 4;
inlay_depth_mm = 1.2;
piece = "composite";
$fn = 48;

module outline() {
    hull() {
        translate([width_mm*0.35, width_mm/2]) circle(r=width_mm*0.35);
        translate([length_mm-width_mm/2, width_mm/2]) circle(r=width_mm/2);
    }
}
module lid() { linear_extrude(thickness_mm) outline(); }
module arrow() {
    translate([20, 17, thickness_mm-inlay_depth_mm])
        linear_extrude(inlay_depth_mm)
            polygon([[-7,-2],[2,-2],[2,-5],[8,0],[2,5],[2,2],[-7,2]]);
}
if (piece == "shell") difference() { lid(); arrow(); }
else if (piece == "mark") arrow();
else lid();
