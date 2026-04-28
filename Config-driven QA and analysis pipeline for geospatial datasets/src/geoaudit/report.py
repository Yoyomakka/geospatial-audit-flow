"""Markdown and HTML report generation."""

from __future__ import annotations

import html
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from jinja2 import Template

from geoaudit.checks import summarize_checks
from geoaudit.models import AnalysisResult, CheckResult

MARKDOWN_TEMPLATE = Template(
    """# {{ project_name }}

{{ project_description }}

## Dataset

| Field | Value |
| --- | --- |
| Input path | `{{ input_path }}` |
| CRS | `{{ crs }}` |
| Row count | {{ row_count }} |
| Geometry types | {{ geometry_types }} |

## Quality Check Summary

| Status | Count |
| --- | ---: |
| PASS | {{ summary.passed }} |
| WARN | {{ summary.warnings }} |
| FAIL | {{ summary.failed }} |
| Total | {{ summary.total }} |

## Quality Checks

| Check | Status | Message |
| --- | --- | --- |
{% for result in check_results -%}
| {{ result.name }} | {{ result.status }} | {{ result.message }} |
{% endfor %}

## Analysis Outputs

{% if analysis_results -%}
| Recipe | Rows | Output |
| --- | ---: | --- |
{% for result in analysis_results -%}
| {{ result.recipe_type }} | {{ result.row_count }} | `{{ result.output_path }}` |
{% endfor %}
{% else -%}
No analysis outputs were generated.
{% endif %}

## Map

{% if map_output -%}
Interactive preview map: `{{ map_output }}`
{% else -%}
No preview map was generated.
{% endif %}

## Suggested Next Steps

{% if summary.failed > 0 -%}
- Resolve failed checks before publishing or using this dataset for decision-making.
{% endif -%}
{% if summary.warnings > 0 -%}
- Review warning checks and decide whether configured fixes are appropriate.
{% endif -%}
- Inspect generated CSV outputs for expected totals.
- Open the preview map and visually spot-check geometry placement.
"""
)


def generate_markdown_report(
    project_config: Mapping[str, Any],
    check_results: Sequence[CheckResult],
    analysis_results: Sequence[AnalysisResult],
    output_path: str | Path,
    dataset_info: Mapping[str, Any] | None = None,
    map_output: str | Path | None = None,
) -> None:
    """Generate a Markdown workflow report."""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    project = project_config.get("project", {})
    input_config = project_config.get("input", {})
    info = dataset_info or {}
    summary = summarize_checks(list(check_results))
    geometry_types = _geometry_types_from_results(check_results)
    analysis_rows = [
        {
            "recipe_type": result.recipe_type,
            "row_count": result.row_count,
            "output_path": _display_path(result.output_path),
        }
        for result in analysis_results
    ]

    markdown = MARKDOWN_TEMPLATE.render(
        project_name=project.get("name", "Geo Audit Report")
        if isinstance(project, Mapping)
        else "Geo Audit Report",
        project_description=project.get("description", "")
        if isinstance(project, Mapping)
        else "",
        input_path=input_config.get("path", "unknown")
        if isinstance(input_config, Mapping)
        else "unknown",
        crs=info.get("crs", "unknown"),
        row_count=info.get("row_count", "unknown"),
        geometry_types=geometry_types,
        summary=summary,
        check_results=check_results,
        analysis_results=analysis_rows,
        map_output=_display_path(map_output) if map_output else "",
    )
    destination.write_text(markdown.strip() + "\n", encoding="utf-8")


def generate_html_report(markdown_path: str | Path, output_path: str | Path) -> None:
    """Generate a simple standalone HTML report from Markdown."""
    markdown = Path(markdown_path).read_text(encoding="utf-8")
    body = _markdown_to_html(markdown)
    html_report = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Geo Audit Report</title>
  <style>
    body {{
      color: #1f2937;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.55;
      margin: 2rem auto;
      max-width: 960px;
      padding: 0 1rem;
    }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #d1d5db; padding: 0.45rem 0.6rem; text-align: left; }}
    th {{ background: #f3f4f6; }}
    code {{ background: #f3f4f6; border-radius: 4px; padding: 0.1rem 0.25rem; }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(html_report, encoding="utf-8")


def _geometry_types_from_results(check_results: Sequence[CheckResult]) -> str:
    for result in check_results:
        if result.name == "geometry_types" and isinstance(result.value, dict):
            return ", ".join(f"{key}: {value}" for key, value in result.value.items())
    return "unknown"


def _markdown_to_html(markdown: str) -> str:
    lines = markdown.splitlines()
    html_lines: list[str] = []
    in_table = False
    in_list = False

    for index, line in enumerate(lines):
        stripped = line.strip()
        next_line = lines[index + 1].strip() if index + 1 < len(lines) else ""

        if not stripped:
            if in_table:
                html_lines.append("</tbody></table>")
                in_table = False
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            continue

        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [_format_inline(cell.strip()) for cell in stripped.strip("|").split("|")]
            if "---" in stripped:
                continue
            if not in_table:
                html_lines.append("<table>")
                if next_line.startswith("|") and "---" in next_line:
                    html_lines.append("<thead><tr>")
                    html_lines.extend(f"<th>{cell}</th>" for cell in cells)
                    html_lines.append("</tr></thead><tbody>")
                else:
                    html_lines.append("<tbody>")
                in_table = True
            elif not (next_line.startswith("|") and "---" in next_line):
                html_lines.append("<tr>")
                html_lines.extend(f"<td>{cell}</td>" for cell in cells)
                html_lines.append("</tr>")
            continue

        if in_table:
            html_lines.append("</tbody></table>")
            in_table = False

        if stripped.startswith("- "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{_format_inline(stripped[2:])}</li>")
            continue

        if in_list:
            html_lines.append("</ul>")
            in_list = False

        if stripped.startswith("# "):
            html_lines.append(f"<h1>{_format_inline(stripped[2:])}</h1>")
        elif stripped.startswith("## "):
            html_lines.append(f"<h2>{_format_inline(stripped[3:])}</h2>")
        else:
            html_lines.append(f"<p>{_format_inline(stripped)}</p>")

    if in_table:
        html_lines.append("</tbody></table>")
    if in_list:
        html_lines.append("</ul>")
    return "\n".join(html_lines)


def _format_inline(text: str) -> str:
    escaped = html.escape(text)
    parts = escaped.split("`")
    for index in range(1, len(parts), 2):
        parts[index] = f"<code>{parts[index]}</code>"
    return "".join(parts)


def _display_path(path: str | Path) -> str:
    path_obj = Path(path)
    try:
        return path_obj.relative_to(Path.cwd()).as_posix()
    except ValueError:
        return str(path_obj)
