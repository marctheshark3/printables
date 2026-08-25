# Wet-Service Fixtures

Use this reference for faucet aids, water guides, soap accessories, drain parts, and other prints that remain wet.

## Design contract

1. Declare `product_class: wet-fixture`, `service_environment: wet`, `expected_components`, and the exact print orientation.
2. Every water path must be visible, wipeable, and continuously drain to an open outlet. No blind pockets, capped channels, or trapped fastener cavities.
3. Use PETG or another explicitly justified wet-service material. PLA is acceptable only for a short fit check.
4. Retention must be mechanical. Friction-only and adhesive-only mounts are not production retention around a child or active water stream.
5. Keep metal hardware and hard printed edges off chrome and porcelain. Use a replaceable compliant pad where the load path touches the fixture.
6. Use generous radii on touch edges. Treat the outlet and any child-facing edge as a contact surface.
7. Keep the drain, overflow, handle sweep, and shutoff access clear.

## Fit evidence

- `measured`: direct caliper/ruler dimension with stated uncertainty.
- `from-user`: a dimension explicitly supplied by the user.
- `fit-tested`: a coupon or prior print was physically tried on the target.
- `assumed`: photo-derived or nominal. This may drive a non-precision adjustable feature, but it cannot close a precision production fit.
- `none`: the design intentionally avoids a precision mating interface.

Set `fit_required: yes` only when the STL depends on a precision mating dimension. The DFM gate blocks required fits whose status is not measured, from-user, or fit-tested.

## CAD and print defaults

- Minimum water-channel wall: 3.0 mm; use 3.6-4.0 mm for a long cantilever.
- Minimum open channel depth: 12 mm unless flow testing supports less.
- Internal fall: at least 2 degrees with tolerance margin; 4-6 degrees is safer for a removable sink guide.
- Cable-tie slot: actual tie width/thickness plus at least 0.5 mm each direction; round slot ends.
- Print water channels open-up when possible. Avoid supports in wetted surfaces.
- Prefer a flat, broad bed face and four or more walls for a child-adjacent cantilever.

These are defaults, not measurements. Record every target-specific deviation in `docs/DESIGN.md`.

## Required verification

- Mesh: closed welded-edge topology, consistent orientation, intended shell count.
- Dry fit: handles complete their full sweep; outlet remains inside the basin; no porcelain point load.
- Cold-flow test: low flow first, then normal flow; no backflow onto the counter and no retained puddle after shutoff.
- Retention test: wet hands cannot shift the part during intended use. Do not simulate a child climbing or hanging on the part.
- Hygiene: adult can remove, rinse, and inspect every wetted surface.

A generated STL can be geometrically print-ready before the physical dry-fit and flow tests. Label that state accurately; do not call it fit-tested until those tests occur.
