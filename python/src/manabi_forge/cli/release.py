"""``manabi release`` subcommands — stage immutable release assets."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError

from manabi_forge.release import ReleaseBlockedError, prepare_release
from manabi_forge.tex import LatexmkNotFoundError

EXIT_VALIDATION_FAILURE = 1
EXIT_MISSING_DEPENDENCY = 3
EXIT_RIGHTS_BLOCK = 4

app = typer.Typer(
    name="release",
    help="Prepare immutable release assets (spec §18).",
    no_args_is_help=True,
)


def _current_commit(material_dir: Path) -> str:
    git = shutil.which("git")
    if git is None:
        typer.echo("git not found; required for release manifests", err=True)
        raise typer.Exit(EXIT_MISSING_DEPENDENCY)
    completed = subprocess.run(  # noqa: S603 -- 引数配列 + 解決済みバイナリで実行
        [git, "-C", str(material_dir), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if completed.returncode != 0:
        msg = f"cannot resolve git commit: {completed.stderr.strip()}"
        raise typer.BadParameter(msg)
    return completed.stdout.strip()


@app.command()
def prepare(
    material_dir: Annotated[
        Path,
        typer.Argument(help="Approved material directory."),
    ],
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit the result as JSON."),
    ] = False,
) -> None:
    """Build and stage release assets for one approved material (spec §13.9, §18).

    レビュー未通過・未承認の教材は拒否する(exit 4)。アセットは
    build/release/<id>-v<version>/ に生成され、リポジトリにはコミットしない。
    """
    if not (material_dir / "material.yaml").is_file():
        msg = f"not a material directory: {material_dir}"
        raise typer.BadParameter(msg)
    try:
        result = prepare_release(
            material_dir,
            source_commit=_current_commit(material_dir),
        )
    except ReleaseBlockedError as exc:
        # 権利・レビュー・状態によるブロック(spec §16.2: exit 4)
        typer.echo(f"release blocked: {exc}", err=True)
        raise typer.Exit(EXIT_RIGHTS_BLOCK) from exc
    except LatexmkNotFoundError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(EXIT_MISSING_DEPENDENCY) from exc
    except (ValidationError, OSError) as exc:
        msg = f"cannot prepare release: {exc}"
        raise typer.BadParameter(msg) from exc

    if json_output:
        typer.echo(result.model_dump_json(indent=2))
    else:
        typer.echo(f"{result.tag}: {len(result.assets)} assets")
        for asset in result.assets:
            typer.echo(f"  {asset}")
