"""``manabi tex`` subcommands — build material PDFs with LuaLaTeX."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
import yaml
from pydantic import ValidationError

from manabi_forge.tex import LatexmkNotFoundError, build_material

EXIT_VALIDATION_FAILURE = 1
EXIT_MISSING_DEPENDENCY = 3

app = typer.Typer(
    name="tex",
    help="Build and inspect material PDFs.",
    no_args_is_help=True,
)


@app.command()
def build(
    material_dir: Annotated[
        Path,
        typer.Argument(help="Material directory containing source/main.tex."),
    ],
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit the build report as JSON."),
    ] = False,
) -> None:
    """Build one material's PDF (latexmk + LuaLaTeX, shell escape disabled)."""
    if not (material_dir / "material.yaml").is_file():
        # 対象が教材ディレクトリでないのは検証失敗ではなく使用法エラー(exit 2)
        msg = f"not a material directory (material.yaml not found): {material_dir}"
        raise typer.BadParameter(msg)
    try:
        result = build_material(material_dir)
    except LatexmkNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(EXIT_MISSING_DEPENDENCY) from exc
    except (ValidationError, yaml.YAMLError) as exc:
        msg = f"invalid material.yaml in {material_dir}: {exc}"
        raise typer.BadParameter(msg) from exc

    if json_output:
        typer.echo(result.model_dump_json(indent=2))
    else:
        status = "ok" if result.ok else "failed"
        typer.echo(f"{result.material_id} ({result.template}): {status}")
        if result.pdf_path:
            typer.echo(f"  pdf: {result.pdf_path}")
        if result.missing_characters:
            typer.echo(f"  missing characters: {result.missing_characters}")
        if result.overfull_count:
            typer.echo(f"  overfull boxes: {result.overfull_count}")
        if not result.ok and result.log_tail:
            typer.echo(result.log_tail)

    if not result.ok:
        raise typer.Exit(EXIT_VALIDATION_FAILURE)
