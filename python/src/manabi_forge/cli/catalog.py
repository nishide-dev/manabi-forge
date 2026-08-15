"""``manabi catalog`` subcommands — generate the public catalog.json."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
import yaml
from pydantic import ValidationError

from manabi_forge.catalog import build_catalog, render_catalog_json
from manabi_forge.schema_export import find_repo_root

EXIT_VALIDATION_FAILURE = 1

app = typer.Typer(
    name="catalog",
    help="Build the static catalog consumed by Manabi Library.",
    no_args_is_help=True,
)


@app.command()
def build(
    out: Annotated[
        Path | None,
        typer.Option(
            "--out",
            help="Output path (default: <repo>/web/public/catalog.json).",
            dir_okay=False,
        ),
    ] = None,
    include_drafts: Annotated[
        bool,
        typer.Option(
            "--include-drafts",
            help="開発プレビュー用に未承認教材も含める。公開デプロイでは使わない。",
        ),
    ] = False,
) -> None:
    """Build catalog.json from committed materials (spec §18.1)."""
    root = find_repo_root()
    materials_root = root / "materials"
    if not materials_root.is_dir():
        msg = f"materials root not found: {materials_root}"
        raise typer.BadParameter(msg)

    try:
        catalog = build_catalog(materials_root, include_drafts=include_drafts)
    except (ValidationError, yaml.YAMLError) as exc:
        typer.echo(f"failed to read material manifests: {exc}", err=True)
        raise typer.Exit(EXIT_VALIDATION_FAILURE) from exc

    out_path = out if out is not None else root / "web" / "public" / "catalog.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_catalog_json(catalog), encoding="utf-8")
    typer.echo(f"wrote {out_path} ({len(catalog.materials)} materials)")
    if include_drafts:
        typer.echo("note: includes drafts — do not deploy this catalog publicly")
