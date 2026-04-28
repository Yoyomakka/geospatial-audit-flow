"""Typed result models used throughout geo-audit-flow."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

CheckStatus = Literal["PASS", "WARN", "FAIL"]


@dataclass(frozen=True)
class CheckResult:
    """Result from one quality check."""

    name: str
    status: CheckStatus
    message: str
    value: Any | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary."""
        return asdict(self)


@dataclass(frozen=True)
class CheckSummary:
    """Aggregate counts for a set of quality checks."""

    total: int
    passed: int
    warnings: int
    failed: int

    def to_dict(self) -> dict[str, int]:
        """Return a JSON-serializable dictionary."""
        return asdict(self)


@dataclass(frozen=True)
class AnalysisResult:
    """Result from one analysis recipe."""

    recipe_type: str
    output_path: Path
    row_count: int
    message: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary."""
        data = asdict(self)
        data["output_path"] = str(self.output_path)
        return data


@dataclass(frozen=True)
class WorkflowResult:
    """Summary of a completed workflow run."""

    check_results: list[CheckResult]
    analysis_results: list[AnalysisResult]
    cleaned_path: Path | None = None
    map_path: Path | None = None
    report_paths: list[Path] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serializable dictionary."""
        return {
            "check_results": [result.to_dict() for result in self.check_results],
            "analysis_results": [result.to_dict() for result in self.analysis_results],
            "cleaned_path": str(self.cleaned_path) if self.cleaned_path else None,
            "map_path": str(self.map_path) if self.map_path else None,
            "report_paths": [str(path) for path in self.report_paths],
        }
