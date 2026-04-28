from __future__ import annotations

from pathlib import Path

import pytest

from geoaudit.config import get_output_dir, load_config, validate_config


def test_load_and_validate_config(tmp_path: Path) -> None:
    data_path = Path("tests/fixtures/valid_points.geojson").resolve()
    config_path = tmp_path / "config.yml"
    config_path.write_text(
        f"""
project:
  name: test
input:
  path: {data_path.as_posix()}
  layer: null
  crs: EPSG:4326
output:
  dir: {tmp_path.as_posix()}/outputs
checks:
  crs: true
""",
        encoding="utf-8",
    )

    config = load_config(config_path)
    validate_config(config)

    assert config["project"]["name"] == "test"
    assert get_output_dir(config).exists()


def test_validate_config_rejects_missing_input(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yml"
    config_path.write_text(
        f"""
input:
  path: {tmp_path.as_posix()}/missing.geojson
output:
  dir: {tmp_path.as_posix()}/outputs
checks:
  crs: true
""",
        encoding="utf-8",
    )
    config = load_config(config_path)

    with pytest.raises(ValueError, match="Input dataset does not exist"):
        validate_config(config)
