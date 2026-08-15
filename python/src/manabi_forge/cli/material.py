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
    """Find every material root directory (containing material.yaml) under ``root``.

    教材ディレクトリ内(source/ など)に紛れ込んだ material.yaml を独立教材と
    誤認しないよう、既に発見した教材ルートの配下は除外する。
    """
    if not root.is_dir():
        return []
    candidates = sorted(path.parent for path in root.rglob("material.yaml"))
    roots: list[Path] = []
    for candidate in candidates:  # sorted なので親が先に現れる
        if not any(candidate.is_relative_to(found) for found in roots):
            roots.append(candidate)
    return roots


def _resolve_targets(paths: list[Path]) -> list[Path]:
    if paths:
        return paths
    materials_root = find_repo_root() / "materials"
    if not materials_root.is_dir():
        # 既定走査対象が丸ごと欠けているのは検証失敗ではなく構成エラー
        # (spec §16.2: usage/configuration error = 2)
        msg = f"materials root not found: {materials_root}"
        raise typer.BadParameter(msg)
    return discover_material_dirs(materials_root)


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
        errors = warnings = 0
        for material in report.materials:
            material_errors = [
                issue for issue in material.issues if issue.level is IssueLevel.ERROR
            ]
            errors += len(material_errors)
            warnings += len(material.issues) - len(material_errors)
            status = "ok" if not material_errors else "errors"
            typer.echo(f"{material.path}: {status}")
            for issue in material.issues:
                typer.echo(
                    f"  [{issue.level.value}] {issue.code} ({issue.location}): "
                    f"{issue.message}",
                )
        typer.echo(
            f"{len(report.materials)} materials, {errors} errors, {warnings} warnings",
        )

    if report.has_errors:
        raise typer.Exit(EXIT_VALIDATION_FAILURE)
