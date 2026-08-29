// Printed ISO metric coarse thread — explicit opt-in only.
// Default fastening is heat-set inserts (see insert_boss.scad).
// Do not include this module unless PRINT_SPEC opts into printed thread.

printed_thread = false;  // opt-in
thread_major_d_mm = 3.0; // M3 coarse
thread_pitch_mm = 0.5;
thread_len_mm = 8;
$fn = 48;

assert(printed_thread == true, "printed thread is opt-in; default is heat-set");

module iso_metric_coarse_bolt() {
  // Placeholder helix; replace with a measured or datasheet profile before export.
  cylinder(d = thread_major_d_mm, h = thread_len_mm);
}

iso_metric_coarse_bolt();
