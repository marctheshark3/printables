from __future__ import annotations

import importlib.util
from copy import deepcopy
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT.parent / "3d-print-design-brief" / "scripts" / "validate_print_spec.py"
TEMPLATE = ROOT.parent / "3d-print-design-brief" / "templates" / "PRINT_SPEC.yaml"
spec = importlib.util.spec_from_file_location("validate_print_spec", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def valid_spec():
    return yaml.safe_load(TEMPLATE.read_text())


def test_template_passes_contract():
    assert module.validate(valid_spec()) == []


def test_rejects_non_parametric_backend():
    data = valid_spec()
    data["cad"]["parametric"] = False
    assert "cad.parametric must be true" in module.validate(data)


def test_rejects_overlapping_solids_policy():
    data = valid_spec()
    data["geometry"]["overlapping_solids_allowed"] = True
    assert "geometry.overlapping_solids_allowed must be false" in module.validate(data)


def test_rejects_ambiguous_or_missing_shell_contract():
    data = valid_spec()
    data["geometry"]["stl_files"][0].pop("expected_shells")
    errors = module.validate(data)
    assert "geometry.stl_files[0].expected_shells is required" in errors
    assert "geometry.stl_files[0].expected_shells must be an integer >= 1" in errors


def test_rejects_assumed_required_fit():
    data = valid_spec()
    data["fit"]["evidence"] = "assumed"
    assert any("required fit needs measured" in error for error in module.validate(data))


def test_rejects_dimension_without_tolerance():
    data = valid_spec()
    data["dimensions"][0].pop("tolerance_mm")
    assert "dimensions[0].tolerance_mm is required" in module.validate(data)


def test_rejects_features_smaller_than_two_nozzle_widths():
    data = valid_spec()
    data["geometry"]["min_wall_mm"] = 0.6
    data["geometry"]["min_feature_mm"] = 0.6
    errors = module.validate(data)
    assert "geometry.min_wall_mm must be at least 2x nozzle_mm" in errors
    assert "geometry.min_feature_mm must be at least 2x nozzle_mm" in errors


def test_rejects_wet_pla_without_drainage():
    data = valid_spec()
    data["service"]["environment"] = "wet"
    data["service"]["drainage"] = "none"
    data["manufacturing"]["material"] = "PLA"
    errors = module.validate(data)
    assert "wet service requires positive drainage" in errors
    assert "wet service cannot use PLA" in errors


def test_rejects_paths_outside_project():
    data = valid_spec()
    data["cad"]["source_files"] = ["../shared/part.scad"]
    data["geometry"]["stl_files"][0]["path"] = "/tmp/part.stl"
    errors = module.validate(data)
    assert any("cad.source_files" in error and "project-relative" in error for error in errors)
    assert any("geometry.stl_files[0].path" in error and "project-relative" in error for error in errors)


def test_check_files_is_fail_closed(tmp_path):
    data = valid_spec()
    errors = module.validate(data, project=tmp_path, check_files=True)
    assert any("declared file does not exist" in error for error in errors)
