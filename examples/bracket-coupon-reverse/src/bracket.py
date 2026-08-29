"""Parametric rebuild from reverse IR. CadQuery / OCC. Millimetres."""
from pathlib import Path

# Named millimetre parameters (reverse IR / PRINT_SPEC.yaml).
depth_mm = 30.000000
extrude_depth_mm = 12.000000
height_mm = 12.000000
hole_f2_d_mm = 4.200000
hole_f3_d_mm = 4.200000
hole_f4_d_mm = 4.200000
width_mm = 40.000000
s1_ox_mm = -2.169780
s1_oy_mm = -2.493724
s1_oz_mm = 6.000000
s1_p0_u_mm = -16.527843
s1_p0_v_mm = -17.807164
s1_p1_u_mm = 11.540395
s1_p1_v_mm = -17.807164
s1_p2_u_mm = 12.154805
s1_p2_v_mm = -17.478749
s1_p3_u_mm = 12.483220
s1_p3_v_mm = -16.864339
s1_p4_u_mm = 12.483220
s1_p4_v_mm = 21.203899
s1_p5_u_mm = 12.154805
s1_p5_v_mm = 21.818309
s1_p6_u_mm = 11.540395
s1_p6_v_mm = 22.146724
s1_p7_u_mm = 1.472157
s1_p7_v_mm = 22.146724
s1_p8_u_mm = 0.857747
s1_p8_v_mm = 21.818309
s1_p9_u_mm = 0.529332
s1_p9_v_mm = 21.203899
s1_p10_u_mm = 0.506276
s1_p10_v_mm = -5.830220
s1_p11_u_mm = -16.527843
s1_p11_v_mm = -5.853276
s1_p12_u_mm = -17.142253
s1_p12_v_mm = -6.181691
s1_p13_u_mm = -17.470668
s1_p13_v_mm = -6.796101
s1_p14_u_mm = -17.470668
s1_p14_v_mm = -16.864339
s1_p15_u_mm = -17.142253
s1_p15_v_mm = -17.478749
hole_f2_u_mm = 6.506284
hole_f2_v_mm = -3.830228
hole_f2_x_mm = -6.000008
hole_f2_y_mm = -9.000008
hole_f3_u_mm = -10.493716
hole_f3_v_mm = -11.830228
hole_f3_x_mm = -14.000008
hole_f3_y_mm = 7.999992
hole_f4_u_mm = 6.506284
hole_f4_v_mm = 15.169772
hole_f4_x_mm = 12.999992
hole_f4_y_mm = -9.000008

def project_root():
    return Path(__file__).resolve().parent.parent

def build():
    import cadquery as cq
    plane = cq.Plane(
        origin=cq.Vector(s1_ox_mm, s1_oy_mm, s1_oz_mm),
        xDir=cq.Vector(0.000000, -1.000000, 0.000000),
        normal=cq.Vector(0.000000, 0.000000, 1.000000),
    )
    wp = cq.Workplane(plane)
    wp = wp.moveTo(s1_p0_u_mm, s1_p0_v_mm)
    wp = wp.lineTo(s1_p1_u_mm, s1_p1_v_mm)
    wp = wp.lineTo(s1_p2_u_mm, s1_p2_v_mm)
    wp = wp.lineTo(s1_p3_u_mm, s1_p3_v_mm)
    wp = wp.lineTo(s1_p4_u_mm, s1_p4_v_mm)
    wp = wp.lineTo(s1_p5_u_mm, s1_p5_v_mm)
    wp = wp.lineTo(s1_p6_u_mm, s1_p6_v_mm)
    wp = wp.lineTo(s1_p7_u_mm, s1_p7_v_mm)
    wp = wp.lineTo(s1_p8_u_mm, s1_p8_v_mm)
    wp = wp.lineTo(s1_p9_u_mm, s1_p9_v_mm)
    wp = wp.lineTo(s1_p10_u_mm, s1_p10_v_mm)
    wp = wp.lineTo(s1_p11_u_mm, s1_p11_v_mm)
    wp = wp.lineTo(s1_p12_u_mm, s1_p12_v_mm)
    wp = wp.lineTo(s1_p13_u_mm, s1_p13_v_mm)
    wp = wp.lineTo(s1_p14_u_mm, s1_p14_v_mm)
    wp = wp.lineTo(s1_p15_u_mm, s1_p15_v_mm)
    wp = wp.close()
    solid = wp.extrude(-1.0 * float(extrude_depth_mm))
    cutter = (
        cq.Workplane(plane)
        .moveTo(hole_f2_u_mm, hole_f2_v_mm)
        .circle(hole_f2_d_mm / 2.0)
        .extrude(-1.0 * (float(extrude_depth_mm) + 2.0))
    )
    solid = solid.cut(cutter)
    cutter = (
        cq.Workplane(plane)
        .moveTo(hole_f3_u_mm, hole_f3_v_mm)
        .circle(hole_f3_d_mm / 2.0)
        .extrude(-1.0 * (float(extrude_depth_mm) + 2.0))
    )
    solid = solid.cut(cutter)
    cutter = (
        cq.Workplane(plane)
        .moveTo(hole_f4_u_mm, hole_f4_v_mm)
        .circle(hole_f4_d_mm / 2.0)
        .extrude(-1.0 * (float(extrude_depth_mm) + 2.0))
    )
    solid = solid.cut(cutter)
    return solid

def main():
    import cadquery as cq
    root = project_root()
    solid = build()
    step = root / 'step' / 'bracket.step'
    stl = root / 'stl' / 'bracket.stl'
    step.parent.mkdir(parents=True, exist_ok=True)
    stl.parent.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(solid, str(step))
    cq.exporters.export(solid, str(stl))
    print('exported', step, stl)

if __name__ in {'__main__', Path(__file__).stem}:
    main()
