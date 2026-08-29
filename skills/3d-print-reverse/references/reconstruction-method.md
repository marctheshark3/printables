# Reconstruction method

Kanrog Creations, [STL to STEP — the proper way](https://www.youtube.com/watch?v=wEN89D1w4JA&t=61s). Reconstruction from a reference mesh, not triangle conversion.

1. Import the STL as **reference only**. Do not convert it.
2. Align to world, millimetres.
3. Measure (axis-aligned lengths, radii, chamfers).
4. Sketch on real planes; project mesh vertices as construction.
5. Rebuild with extrude / revolve / loft / boolean / hole / fillet / chamfer / mirror.
6. Export analytic STEP (planes, cylinders, cones, spheres, fillets — not one face per triangle).
7. Compare rebuilt solid vs input mesh. Deviation is the proof.

There is no automatic converter that produces a proper CAD file. Recreate the part.

`mesh.to_shape` in 10-X-eng/vibecad is a faceted OCC snapshot. It is not design intent and must never be treated as reverse-engineered STEP.
