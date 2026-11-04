"""Sample region occupancies against the independently exported composite body."""
from __future__ import annotations

from itertools import product
from pathlib import Path

from overlap import point_in_mesh, tris_aabb
from stl_io import bbox_and_volume, load_binary_stl, tri_normal
from validate_stl import audit_mesh, report


def _samples(tris):
    box = tris_aabb(tris)
    inset = max(0.0001, min(box[i + 3] - box[i] for i in range(3)) * 0.001)
    for tri in tris[::max(1, len(tris) // 256)]:
        normal = tri_normal(*tri)
        point = tuple(sum(v[i] for v in tri) / 3 - inset * normal[i] for i in range(3))
        if point_in_mesh(point, tris):
            yield point
    for indices in product(range(1, 8), repeat=3):
        point = tuple(box[i] + (box[i + 3] - box[i]) * indices[i] / 8 for i in range(3))
        if point_in_mesh(point, tris):
            yield point


def partition_errors(composite, regions) -> list[str]:
    errors = []
    volume = bbox_and_volume(composite)[2]
    region_volume = sum(bbox_and_volume(mesh)[2] for mesh in regions)
    if abs(region_volume - volume) > max(0.001, abs(volume) * 0.0001):
        errors.append("material region volumes do not match the composite body")
    # Probe both sides of every material boundary, as well as composite interior.
    # Shared boundary contact is legal; positive interior occupancy is exclusive.
    for mesh in regions:
        for point in _samples(mesh):
            if not point_in_mesh(point, composite):
                return errors + ["material region extends outside the composite body"]
            if sum(point_in_mesh(point, other) for other in regions) > 1:
                return errors + ["material regions overlap in their interiors"]
    for point in _samples(composite):
        count = sum(point_in_mesh(point, mesh) for mesh in regions)
        if count == 0:
            return errors + ["composite has uncovered material occupancy"]
        if count > 1:
            return errors + ["material regions overlap in their interiors"]
    return errors


def audit_material_regions(project: Path, spec) -> list[str]:
    plan = spec.multi_material
    if plan is None or not plan.regions:
        return []
    errors = []
    for body in spec.stl_files:
        regions = plan.regions_for(body.body)
        if not regions:
            continue
        print(f"=== material regions: {body.body} (sampled occupancy, not exact-kernel) ===")
        meshes = []
        for region in regions:
            hard, warn, info = audit_mesh(
                project / region.path, expected_shells=region.expected_shells,
                build=spec.build_volume_mm, product_class="other",
                orientation=spec.orientation, up_axis=spec.up_axis,
                min_feature_mm=spec.nozzle_mm * 2, min_wall_mm=region.min_wall_mm,
                max_overhang_deg=spec.max_overhang_deg,
            )
            report(hard, warn, info)
            if hard:
                errors.append(f"material region {region.id} failed mesh validation")
            else:
                meshes.append(load_binary_stl(project / region.path)[1])
        if len(meshes) == len(regions):
            composite = load_binary_stl(project / body.path)[1]
            errors.extend(f"{body.body}: {error}" for error in partition_errors(composite, meshes))
    return errors
