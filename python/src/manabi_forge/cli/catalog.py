"""``manabi catalog`` subcommands — generate the public catalog.json."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from manabi_forge.catalog import CatalogBuildError, build_catalog, render_catalog_json
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
    materials_root: Annotated[
        Path | None,
        typer.Option(
            "--materials-root",
            help="Materials tree to build from (default: <repo>/materials).",
            file_okay=False,
        ),
    ] = None,
) -> None:
    """Build catalog.json from committed materials (spec §18.1)."""
    root = find_repo_root()
    resolved_materials = (
        materials_root if materials_root is not None else root / "materials"
    )
    if not resolved_materials.is_dir():
        msg = f"materials root not found: {resolved_materials}"
        raise typer.BadParameter(msg)

    try:
        catalog = build_catalog(resolved_materials, include_drafts=include_drafts)
    except CatalogBuildError as exc:
        typer.echo(f"catalog build failed: {exc}", err=True)
        raise typer.Exit(EXIT_VALIDATION_FAILURE) from exc
    except OSError as exc:
        # ファイルが読めないのは構成エラー(spec §16.2: exit 2)
        msg = f"cannot read material manifest: {exc}"
        raise typer.BadParameter(msg) from exc

    out_path = out if out is not None else root / "web" / "public" / "catalog.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_catalog_json(catalog), encoding="utf-8")
    typer.echo(f"wrote {out_path} ({len(catalog.materials)} materials)")
    if include_drafts:
        typer.echo("note: includes drafts — do not deploy this catalog publicly")
