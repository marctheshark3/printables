#!/usr/bin/env python3
"""Optional extra extra: headless table-flat 100 mm roll from PRINT_SPEC.

Skipped when the mujoco package is absent. Isaac/Gazebo are not used.
PRINT_SPEC remains the contract; this run does not grant sim2real.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
BRIEF = SCRIPTS.parent.parent / "3d-print-design-brief" / "scripts"
VALIDATE = SCRIPTS.parent.parent / "3d-print-validate" / "scripts"
for path in (str(BRIEF), str(VALIDATE)):
    if path not in sys.path:
        sys.path.insert(0, path)

from print_spec import CalibrationCoupon, PrintSpec, load_spec  # noqa: E402


def mujoco_available() -> bool:
    return importlib.util.find_spec("mujoco") is not None


def _dim_mm(spec: PrintSpec, parameter: str) -> float | None:
    for dim in spec.dimensions:
        if dim.parameter == parameter:
            return float(dim.value_mm)
    return None


def _coupon(spec: PrintSpec, ctype: str) -> CalibrationCoupon | None:
    matches = [item for item in spec.calibration if item.type == ctype]
    if len(matches) != 1:
        return None
    return matches[0]


def roll_model_errors(spec: PrintSpec) -> list[str]:
    errors: list[str] = []
    if spec.sim_scene is None:
        errors.append("roll extra extra needs sim.scene")
    if _coupon(spec, "mass") is None:
        errors.append("roll extra extra needs exactly one mass calibration coupon")
    if _coupon(spec, "friction") is None:
        errors.append("roll extra extra needs exactly one friction calibration coupon")
    for parameter in ("wheel_od_mm", "chassis_length_mm", "chassis_width_mm"):
        if _dim_mm(spec, parameter) is None:
            errors.append(f"roll extra extra needs dimension {parameter}")
    return errors


def build_roll_mjcf(spec: PrintSpec) -> str:
    """Named-scene MJCF from required PRINT_SPEC calibration and dimensions."""
    missing = roll_model_errors(spec)
    if missing:
        raise ValueError("; ".join(missing))
    mass = _coupon(spec, "mass")
    friction = _coupon(spec, "friction")
    assert mass is not None and friction is not None and spec.sim_scene is not None
    units = mass.units.lower()
    mass_g = mass.magnitude * (1000.0 if units in {"kg"} else 1.0)
    mu = friction.magnitude
    wheel_od = _dim_mm(spec, "wheel_od_mm")
    length_mm = _dim_mm(spec, "chassis_length_mm")
    width_mm = _dim_mm(spec, "chassis_width_mm")
    assert wheel_od is not None and length_mm is not None and width_mm is not None
    wheel_r = wheel_od / 2000.0
    mass_kg = mass_g / 1000.0
    half_l = length_mm / 2000.0
    half_w = width_mm / 2000.0
    z = wheel_r
    scene = spec.sim_scene.id
    gz = spec.sim_scene.gravity_mm_s2[2] / 1000.0
    return f"""<mujoco model="{spec.part_name}-roll">
  <!-- extra extra; emitted from PRINT_SPEC; not a contract -->
  <compiler angle="degree"/>
  <option gravity="0 0 {gz:.5f}" timestep="0.002"/>
  <default>
    <geom friction="{mu:.4f} {mu:.4f} 0.001"/>
  </default>
  <worldbody>
    <geom name="{scene}" type="plane" size="2 2 0.05"/>
    <body name="rover" pos="0 0 {z:.5f}">
      <joint name="roll" type="slide" axis="1 0 0"/>
      <geom type="box" size="{half_l:.5f} {half_w:.5f} 0.006" mass="{mass_kg:.5f}"/>
      <body name="wheel_l" pos="0 {-half_w:.5f} {-0.002}">
        <joint name="wheel_left" type="hinge" axis="0 1 0"/>
        <geom type="cylinder" size="{wheel_r:.5f} 0.003" mass="0.01"/>
      </body>
      <body name="wheel_r" pos="0 {half_w:.5f} {-0.002}">
        <joint name="wheel_right" type="hinge" axis="0 1 0"/>
        <geom type="cylinder" size="{wheel_r:.5f} 0.003" mass="0.01"/>
      </body>
    </body>
  </worldbody>
  <actuator>
    <velocity name="left" joint="wheel_left" kv="1" ctrllimited="true" ctrlrange="-20 20"/>
    <velocity name="right" joint="wheel_right" kv="1" ctrllimited="true" ctrlrange="-20 20"/>
  </actuator>
</mujoco>
"""


def commanded_distance_mm(spec: PrintSpec) -> float:
    if spec.sim_roll is None:
        raise ValueError("roll extra extra needs sim.roll.distance_mm")
    return float(spec.sim_roll.distance_mm)


def run_roll(spec: PrintSpec) -> float:
    import mujoco  # noqa: PLC0415 — extra extra only

    xml = build_roll_mjcf(spec)
    model = mujoco.MjModel.from_xml_string(xml)
    data = mujoco.MjData(model)
    target_m = commanded_distance_mm(spec) / 1000.0
    wheel_od = _dim_mm(spec, "wheel_od_mm")
    assert wheel_od is not None
    wheel_r = wheel_od / 2000.0
    omega = 2.0 / max(wheel_r, 1e-6)
    steps = int(2.5 / model.opt.timestep)
    for _ in range(steps):
        data.ctrl[:] = (omega, omega)
        mujoco.mj_step(model, data)
        if float(data.qpos[0]) >= target_m:
            break
    return float(data.qpos[0]) * 1000.0


def main() -> int:
    parser = argparse.ArgumentParser(description="Optional headless 100 mm table-flat roll")
    parser.add_argument("project", type=Path)
    parser.add_argument("--spec", default="docs/PRINT_SPEC.yaml")
    args = parser.parse_args()
    if not mujoco_available():
        print("SKIP: mujoco not installed (extra extra)")
        return 0
    project = args.project.resolve()
    spec, errors = load_spec(project / args.spec, project=project, check_files=False)
    if spec is None or errors:
        for error in errors:
            print(f"HARD: {error}")
        print("RESULT: FAIL")
        return 1
    missing = roll_model_errors(spec)
    if spec.sim_roll is None:
        missing.append("roll extra extra needs sim.roll")
    if missing:
        for error in missing:
            print(f"HARD: {error}")
        print("RESULT: FAIL")
        return 1
    travelled_mm = run_roll(spec)
    target = commanded_distance_mm(spec)
    budget = spec.sim_roll.error_budget_mm
    print(f"INFO: table-flat roll {travelled_mm:.1f} mm (commanded {target:g} mm)")
    if budget is not None and abs(travelled_mm - target) > budget + 1e-6:
        print(f"HARD: roll error exceeds budget {budget:g} mm")
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
