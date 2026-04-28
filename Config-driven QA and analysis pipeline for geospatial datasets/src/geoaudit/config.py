"""Configuration loading and validation."""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path
from typing import Any

import yaml

from geoaudit.utils import ensure_directory, project_base_dir, resolve_path


def load_config(path: str | Path) -> dict[str, Any]:
    """Load a YAML config file."""
    config_path = Path(path).expanduser().resolve()
    if not config_path.exists():
        raise ValueError(f"Config file does not exist: {config_path}")

    with config_path.open("r", encoding="utf-8") as file:
        data = yaml.safe_load(file)

    if not isinstance(data, dict):
        raise ValueError("Config file must contain a YAML mapping at the top level.")

    config: dict[str, Any] = dict(data)
    config["__config_path__"] = str(config_path)
    config["__base_dir__"] = str(config_path.parent)
    return config


def validate_config(config: dict[str, Any]) -> None:
    """Validate the minimum schema needed to run a workflow."""
    input_config = _require_mapping(config, "input")
    output_config = _require_mapping(config, "output")
    checks_config = _require_mapping(config, "checks")

    input_path_raw = input_config.get("path")
    if not input_path_raw:
        raise ValueError("Config field 'input.path' is required.")

    input_path = resolve_path(str(input_path_raw), project_base_dir(config))
    if not input_path.exists():
        raise ValueError(f"Input dataset does not exist: {input_path}")

    output_dir_raw = output_config.get("dir")
    if not output_dir_raw:
        raise ValueError("Config field 'output.dir' is required.")

    output_dir = get_output_dir(config)
    ensure_directory(output_dir)

    if not checks_config:
        raise ValueError("Config section 'checks' must contain at least one enabled check.")

    for optional_section in ("fixes", "analysis", "report", "map", "project"):
        if optional_section in config and config[optional_section] is None:
            raise ValueError(f"Config section '{optional_section}' cannot be null.")


def get_output_dir(config: dict[str, Any]) -> Path:
    """Return the configured output directory, creating it when needed."""
    output_config = _require_mapping(config, "output")
    output_dir_raw = output_config.get("dir")
    if not output_dir_raw:
        raise ValueError("Config field 'output.dir' is required.")

    output_dir = resolve_output_path(config, str(output_dir_raw))
    return ensure_directory(output_dir)


def resolve_config_path(config: dict[str, Any], value: str | Path) -> Path:
    """Resolve a config path using geo-audit-flow's cwd/config-dir behavior."""
    return resolve_path(value, project_base_dir(config))


def resolve_output_path(config: dict[str, Any], value: str | Path) -> Path:
    """Resolve output paths relative to the current run directory."""
    del config
    output_path = Path(value).expanduser()
    if output_path.is_absolute():
        return output_path
    return (Path.cwd() / output_path).resolve()


def _require_mapping(config: MutableMapping[str, Any], key: str) -> dict[str, Any]:
    value = config.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Config section '{key}' is required and must be a mapping.")
    return value
