from __future__ import annotations

import sys
from pathlib import Path

import yaml

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import print_spec as module  # noqa: E402

TEMPLATE = Path(__file__).resolve().parents[1] / "templates" / "PRINT_SPEC.yaml"


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


def test_wet_slots_drainage_passes():
    data = valid_spec()
    data["service"]["environment"] = "wet"
    data["service"]["drainage"] = "slots"
    data["manufacturing"]["material"] = "PETG"
    assert module.validate(data) == []


def test_wet_unknown_drainage_fails():
    data = valid_spec()
    data["service"]["environment"] = "wet"
    data["service"]["drainage"] = "mystery"
    data["manufacturing"]["material"] = "PETG"
    errors = module.validate(data)
    assert any("service.drainage must be one of" in error for error in errors)
    assert "wet service requires positive drainage" in errors


def test_datasheet_required_fit_passes_contract():
    data = valid_spec()
    data["fit"]["evidence"] = "datasheet"
    data["fit"]["coupon"] = "fit/example-bracket-fit-coupon.stl"
    assert module.validate(data) == []


def test_missing_coupon_file_fails(tmp_path):
    data = valid_spec()
    (tmp_path / "src").mkdir()
    (tmp_path / "stl").mkdir()
    (tmp_path / "src/example-bracket.scad").write_text("device_width_mm = 40;\n")
    (tmp_path / "stl/example-bracket.stl").write_bytes(b"solid")
    errors = module.validate(data, project=tmp_path, check_files=True)
    assert any("fit/example-bracket-fit-coupon.stl" in error for error in errors)


def test_parse_spec_roundtrip():
    parsed = module.parse_spec(valid_spec())
    assert parsed.backend == "openscad"
    assert parsed.stl_files[0].expected_shells == 1
    assert parsed.up_axis == "Z"
