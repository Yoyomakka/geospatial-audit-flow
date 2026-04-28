"""Small utility helpers for path and filesystem handling."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any


def ensure_directory(path: str | Path) -> Path:
    """Create a directory if needed and return it as a Path."""
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def project_base_dir(config: Mapping[str, Any]) -> Path:
    """Return the directory that contains the loaded config file."""
    raw = config.get("__base_dir__")
    if raw is None:
        return Path.cwd()
    return Path(str(raw))


def resolve_path(path: str | Path, base_dir: str | Path | None = None) -> Path:
    """Resolve a path against cwd first, then against a config base directory.

    Many users run workflows from the repository root, while others keep all paths
    relative to the config file. Supporting both makes examples and copied project
    folders ergonomic without adding config noise.
    """
    candidate = Path(path).expanduser()
    if candidate.is_absolute():
        return candidate

    cwd_candidate = (Path.cwd() / candidate).resolve()
    if cwd_candidate.exists():
        return cwd_candidate

    if base_dir is not None:
        return (Path(base_dir) / candidate).resolve()

    return cwd_candidate


def make_parent_dir(path: str | Path) -> Path:
    """Ensure the parent directory for a file path exists."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    return file_path
