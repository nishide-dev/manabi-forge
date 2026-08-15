"""``manabi curriculum`` subcommands — validate and query normalized records."""

from __future__ import annotations

from typing import Annotated

import typer
import yaml
from pydantic import ValidationError

from manabi_forge.cli.material import discover_material_dirs
from manabi_forge.curriculum import CurriculumStore, DuplicateCodeError, load_store
from manabi_forge.models import MaterialManifest
from manabi_forge.schema_export import find_repo_root

EXIT_VALIDATION_FAILURE = 1

app = typer.Typer(
    name="curriculum",
    help="Validate and query the normalized curriculum knowledge base.",
    no_args_is_help=True,
)


def _load_repo_store() -> CurriculumStore:
    root = find_repo_root()
    normalized = root / "curriculum" / "normalized"
    if not normalized.is_dir():
        msg = f"normalized curriculum directory not found: {normalized}"
        raise typer.BadParameter(msg)
    return load_store(normalized)


@app.command()
def validate(
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit the report as JSON."),
    ] = False,
) -> None:
    """Validate normalized records and resolve every material's codes.

    公開教材のカリキュラムコードが正規レコードに解決できること(spec §24
    Phase 2 exit criteria)をリポジトリ全体で検査する。
    """
    try:
        store = _load_repo_store()
    except (ValidationError, DuplicateCodeError, yaml.YAMLError) as exc:
        typer.echo(f"curriculum records invalid: {exc}", err=True)
        raise typer.Exit(EXIT_VALIDATION_FAILURE) from exc

    failures: list[dict[str, object]] = []
    root = find_repo_root()
    for material_dir in discover_material_dirs(root / "materials"):
        manifest_path = material_dir / "material.yaml"
        try:
            manifest = MaterialManifest.model_validate(
                yaml.safe_load(manifest_path.read_text(encoding="utf-8")),
            )
        except (ValidationError, yaml.YAMLError):
            # マニフェスト自体の問題は `manabi material validate` が報告する
            continue
        missing = store.missing_codes(manifest.curriculum.codes)
        if missing:
            failures.append({"material": manifest.id, "missing_codes": missing})

    if json_output:
        payload = {
            "records": len(store.records),
            "unresolved": failures,
        }
        typer.echo(yaml.safe_dump(payload, allow_unicode=True, sort_keys=True))
    else:
        typer.echo(f"{len(store.records)} curriculum records loaded")
        for failure in failures:
            typer.echo(
                f"  [error] {failure['material']}: unresolved codes "
                f"{failure['missing_codes']}",
            )
    if failures:
        raise typer.Exit(EXIT_VALIDATION_FAILURE)


@app.command()
def query(
    course: Annotated[
        str | None,
        typer.Option(help="Filter by course (e.g. mathematics-i)."),
    ] = None,
    unit: Annotated[
        str | None,
        typer.Option(help="Filter by unit path segment (e.g. quadratic-functions)."),
    ] = None,
    text: Annotated[
        str | None,
        typer.Option(help="Free-text search over statements and scope notes."),
    ] = None,
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit matching records as JSON."),
    ] = False,
) -> None:
    """Query normalized curriculum records with evidence and uncertainty."""
    store = _load_repo_store()
    results = store.query(course=course, unit=unit, text=text)
    if json_output:
        typer.echo(
            "["
            + ",\n".join(record.model_dump_json(indent=2) for record in results)
            + "]",
        )
        return
    for record in results:
        typer.echo(f"{record.code} [{record.review.status.value}]")
        typer.echo(f"  {' / '.join(record.path)}")
        typer.echo(f"  {record.statement_ja}")
        for note in record.uncertainty_notes:
            typer.echo(f"  (uncertainty) {note}")
    typer.echo(f"{len(results)} records")
