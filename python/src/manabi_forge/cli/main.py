"""Entry point for the ``manabi`` command-line interface.

終了コード規約(spec §16.2): 0 成功 / 1 検証・レビュー失敗 / 2 使用法エラー /
3 外部依存の欠落 / 4 権利・来歴ブロック / 5 内部エラー。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

import typer

from manabi_forge import __version__
from manabi_forge.cli.catalog import app as catalog_app
from manabi_forge.cli.curriculum import app as curriculum_app
from manabi_forge.cli.material import app as material_app
from manabi_forge.cli.release import app as release_app
from manabi_forge.cli.schemas import app as schemas_app
from manabi_forge.cli.tex import app as tex_app
from manabi_forge.cli.verify import app as verify_app
from manabi_forge.doctor import run_checks

if TYPE_CHECKING:
    from manabi_forge.doctor import CheckResult

EXIT_OK = 0
EXIT_VALIDATION_FAILURE = 1
EXIT_MISSING_DEPENDENCY = 3

app = typer.Typer(
    name="manabi",
    help="Curriculum-aware tools for creating reliable learning materials.",
    no_args_is_help=True,
)
app.add_typer(catalog_app)
app.add_typer(curriculum_app)
app.add_typer(material_app)
app.add_typer(release_app)
app.add_typer(schemas_app)
app.add_typer(tex_app)
app.add_typer(verify_app)


@app.command()
def version() -> None:
    """Print the manabi-forge version."""
    typer.echo(__version__)


def _status_label(check: CheckResult) -> str:
    """Return a human-readable status label for one check."""
    if check.ok:
        return "ok"
    return "MISSING" if check.required else "missing (optional)"


@app.command()
def doctor(
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit the report as JSON."),
    ] = False,
) -> None:
    """Check that external tools required by the workflow are available."""
    report = run_checks()
    if json_output:
        typer.echo(report.model_dump_json(indent=2))
    else:
        for check in report.checks:
            line = f"[{_status_label(check)}] {check.name}: {check.detail}"
            if check.hint:
                line += f" -> {check.hint}"
            typer.echo(line)
    if not report.ok:
        raise typer.Exit(EXIT_MISSING_DEPENDENCY)
