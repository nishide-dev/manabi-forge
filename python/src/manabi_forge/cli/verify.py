"""``manabi verify`` subcommands — independent mathematical verification."""

from __future__ import annotations

import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import typer
import yaml
from pydantic import ValidationError

from manabi_forge import __version__
from manabi_forge.models import ItemSpec, ReviewRecord
from manabi_forge.verification import VerificationReport, verify_item
from manabi_forge.verification.math import OutcomeStatus

EXIT_VALIDATION_FAILURE = 1
EXIT_MISSING_DEPENDENCY = 3

app = typer.Typer(
    name="verify",
    help="Independently verify item claims (spec §13.4).",
    no_args_is_help=True,
)


def _current_commit(material_dir: Path) -> str:
    """Resolve the current git commit for the review record."""
    git = shutil.which("git")
    if git is None:
        typer.echo("git not found; required for --record", err=True)
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


def _record_review(
    material_dir: Path,
    report: VerificationReport,
    reviewed_commit: str,
) -> Path:
    """Write the verification result as an immutable automated review record.

    自動レビューは kind: automated としてツール名・バージョンを明示し、
    人間レビューと偽装しない(spec §11.5)。教材の承認は行わない(ADR-004)。
    """
    now = datetime.now(tz=UTC)
    if report.passed:
        result = "passed"
    elif report.failed:
        result = "changes-requested"
    else:
        result = "escalated"
    findings = [
        {
            "severity": "high" if outcome.status is OutcomeStatus.FAILED else "note",
            "location": f"item.verification_checks[{outcome.check_id}]",
            "code": f"verify-{outcome.status.value}",
            "message": outcome.detail,
        }
        for outcome in report.outcomes
        if outcome.status is not OutcomeStatus.PASSED
    ]
    record = ReviewRecord.model_validate(
        {
            "material_id": report.material_id,
            "review_id": f"math-auto-{now:%Y%m%d%H%M%S}",
            "review_type": "mathematics",
            "reviewer": {
                "kind": "automated",
                "name": "manabi-verify-math",
                "tool_version": __version__,
            },
            "reviewed_commit": reviewed_commit,
            "result": result,
            "findings": findings,
            "created_at": now,
        },
    )
    reviews_dir = material_dir / "reviews"
    reviews_dir.mkdir(parents=True, exist_ok=True)
    path = reviews_dir / f"{record.review_id}.yaml"
    path.write_text(
        yaml.safe_dump(
            record.model_dump(mode="json"),
            allow_unicode=True,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


@app.command()
def math(
    material_dir: Annotated[
        Path,
        typer.Argument(help="Material directory containing item.yaml."),
    ],
    json_output: Annotated[
        bool,
        typer.Option("--json", help="Emit the report as JSON."),
    ] = False,
    record: Annotated[
        bool,
        typer.Option(
            "--record",
            help="結果を reviews/ に自動レビューレコードとして記録する。",
        ),
    ] = False,
) -> None:
    """Verify the item's machine-checkable claims with SymPy (spec §13.4).

    合格は「証拠」であり、教材の承認は人間レビュアーのみが行う(ADR-004)。
    終了コード: 0 = 全チェック合格 / 1 = 失敗または escalated(人間レビュー
    要。区別は出力・--json で行う)/ 2 = 構成エラー / 3 = git 欠落。
    """
    item_path = material_dir / "item.yaml"
    if not item_path.is_file():
        msg = f"item.yaml not found in {material_dir}"
        raise typer.BadParameter(msg)
    try:
        item = ItemSpec.model_validate(
            yaml.safe_load(item_path.read_text(encoding="utf-8")),
        )
    except (ValidationError, yaml.YAMLError) as exc:
        msg = f"invalid item.yaml: {exc}"
        raise typer.BadParameter(msg) from exc

    # 記録に必要な前提(git)は検証前に解決し、検証結果の出力後に
    # 使用法エラーで落ちて結果もレコードも失われる事態を防ぐ
    reviewed_commit = _current_commit(material_dir) if record else ""

    report = verify_item(item)

    if json_output:
        typer.echo(report.model_dump_json(indent=2))
    else:
        for outcome in report.outcomes:
            typer.echo(f"[{outcome.status.value}] {outcome.check_id}: {outcome.detail}")
        summary = (
            "passed" if report.passed else "failed" if report.failed else "escalated"
        )
        typer.echo(f"verification result: {summary}")

    if record:
        typer.echo(f"recorded {_record_review(material_dir, report, reviewed_commit)}")

    if not report.passed:
        raise typer.Exit(EXIT_VALIDATION_FAILURE)
