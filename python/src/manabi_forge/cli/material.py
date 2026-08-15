"""``manabi material`` subcommands — structural validation of material directories."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from pydantic import BaseModel, ConfigDict

from manabi_forge.schema_export import find_repo_root
from manabi_forge.validation import IssueLevel, ValidationIssue, validate_material_dir

EXIT_VALIDATION_FAILURE = 1

app = typer.Typer(
    name="material",
    help="Validate and manage material directories.",
    no_args_is_help=True,
)


class MaterialReport(BaseModel):
    """Validation result for one material directory."""

    model_config = ConfigDict(extra="forbid")

    path: str
    issues: list[ValidationIssue]


class ValidateReport(BaseModel):
    """Aggregated validation result across material directories."""

    model_config = ConfigDict(extra="forbid")

    materials: list[MaterialReport]

    @property
    def has_errors(self) -> bool:
        """Return ``True`` when any material has an error-level issue."""
        return any(
            issue.level is IssueLevel.ERROR
            for report in self.materials
            for issue in report.issues
        )


def discover_material_dirs(root: Path) -> list[Path]:
    """Find every material directory (containing material.yaml) under ``root``."""
    if not root.is_dir():
        return []
    return sorted(path.parent for path in root.rglob("material.yaml"))


def _resolve_targets(paths: list[Path]) -> list[Path]:
    if paths:
        return paths
    return discover_material_dirs(find_repo_root() / "materials")


@app.command()
def validate(
    paths: Annotated[
        list[Path] | None,
        typer.Argument(
            help="Material directories (default: every material under <repo>/materials).",
        ),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit the report as JSON."),
    ] = False,
) -> None:
    """Run structural validation (spec §13.3 Stage C) on material directories."""
    targets = _resolve_targets(paths or [])
    report = ValidateReport(
        materials=[
            MaterialReport(
                path=str(target),
                issues=validate_material_dir(target),
            )
            for target in targets
        ],
    )

    if json_output:
        typer.echo(report.model_dump_json(indent=2))
    elif not report.materials:
        typer.echo("no materials found")
    else:
        for material in report.materials:
            status = "ok" if not material.issues else "issues"
            typer.echo(f"{material.path}: {status}")
            for issue in material.issues:
                typer.echo(
                    f"  [{issue.level.value}] {issue.code} ({issue.location}): "
                    f"{issue.message}",
                )

    if report.has_errors:
        raise typer.Exit(EXIT_VALIDATION_FAILURE)
