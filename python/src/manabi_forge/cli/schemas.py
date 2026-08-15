"""``manabi schemas`` subcommands — generate and verify committed JSON Schemas."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from manabi_forge.schema_export import check_schemas, find_repo_root, write_schemas

EXIT_VALIDATION_FAILURE = 1

app = typer.Typer(
    name="schemas",
    help="Generate and verify the committed JSON Schema files.",
    no_args_is_help=True,
)

OutDirOption = Annotated[
    Path | None,
    typer.Option(
        "--out",
        help="Schema directory (default: <repo root>/schemas).",
        file_okay=False,
    ),
]


def _resolve_out_dir(out: Path | None) -> Path:
    """Resolve the schema output directory, defaulting to ``<repo root>/schemas``."""
    return out if out is not None else find_repo_root() / "schemas"


@app.command()
def generate(out: OutDirOption = None) -> None:
    """Regenerate every JSON Schema file from the Pydantic models."""
    for path in write_schemas(_resolve_out_dir(out)):
        typer.echo(f"wrote {path}")


@app.command()
def check(out: OutDirOption = None) -> None:
    """Fail when a committed schema differs from the current models."""
    stale = check_schemas(_resolve_out_dir(out))
    if stale:
        for filename in stale:
            typer.echo(f"stale or missing: {filename}")
        typer.echo("run `manabi schemas generate` and commit the result")
        raise typer.Exit(EXIT_VALIDATION_FAILURE)
    typer.echo("schemas are up to date")
