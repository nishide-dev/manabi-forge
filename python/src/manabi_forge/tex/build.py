"""Build material PDFs with latexmk + LuaLaTeX (spec §9.4, §9.5, §15).

- shell escape は常に無効(spec §15.4, §19.2)
- 外部コマンドは引数配列で実行し、文字列補間シェルを使わない(spec §19.2)
- ビルド成果物は build/ 配下に出力し、リポジトリにはコミットしない(ADR-005)
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from typing import TYPE_CHECKING

import yaml
from pydantic import BaseModel, ConfigDict, Field

from manabi_forge.models import MaterialFormat, MaterialManifest
from manabi_forge.schema_export import find_repo_root

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

#: format ごとのテンプレートディレクトリ(templates/ 配下)。
TEMPLATE_DIRS: dict[MaterialFormat, str] = {
    MaterialFormat.COMMON_TEST_STYLE: "common-test",
    MaterialFormat.GUIDED_EXAMPLE: "guided-example",
    MaterialFormat.WORKSHEET: "worksheet",
}

_MISSING_CHARACTER = re.compile(r"^Missing character: (.+)$", re.MULTILINE)
_OVERFULL_BOX = re.compile(r"^Overfull \\[hv]box", re.MULTILINE)

_BUILD_TIMEOUT_SECONDS = 600


class LatexmkNotFoundError(RuntimeError):
    """Raised when latexmk is not available on PATH."""


class TexBuildResult(BaseModel):
    """Outcome of one material build, including log inspection (spec §13.8)."""

    model_config = ConfigDict(extra="forbid")

    material_id: str
    template: str
    ok: bool
    returncode: int
    pdf_path: str | None = None
    log_path: str | None = None
    missing_characters: list[str] = Field(default_factory=list)
    overfull_count: int = 0
    log_tail: str = ""


def parse_latex_log(log_text: str) -> tuple[list[str], int]:
    """Extract missing characters and overfull box count from a LaTeX log."""
    missing = sorted(set(_MISSING_CHARACTER.findall(log_text)))
    overfull = len(_OVERFULL_BOX.findall(log_text))
    return missing, overfull


def _load_manifest(material_dir: Path) -> MaterialManifest:
    data = yaml.safe_load((material_dir / "material.yaml").read_text(encoding="utf-8"))
    return MaterialManifest.model_validate(data)


def _texinputs(repo_root: Path, template_dir: str, env: Mapping[str, str]) -> str:
    """Compose TEXINPUTS so the shared class and the template resolve."""
    paths = [
        str(repo_root / "templates" / "shared"),
        str(repo_root / "templates" / template_dir),
    ]
    existing = env.get("TEXINPUTS", "")
    # 末尾の空要素は TeX の既定検索パスを維持するために必要
    return os.pathsep.join([*paths, existing])


def build_material(
    material_dir: Path,
    *,
    repo_root: Path | None = None,
    out_root: Path | None = None,
) -> TexBuildResult:
    """Build one material's PDF reproducibly and inspect the log."""
    latexmk = shutil.which("latexmk")
    if latexmk is None:
        msg = "latexmk not found; install TeX Live (see `manabi doctor`)"
        raise LatexmkNotFoundError(msg)

    root = repo_root if repo_root is not None else find_repo_root()
    manifest = _load_manifest(material_dir)
    template_dir = TEMPLATE_DIRS[manifest.classification.format]

    out_dir = (out_root if out_root is not None else root / "build") / manifest.id
    out_dir.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    env["TEXINPUTS"] = _texinputs(root, template_dir, env)

    main_tex = material_dir / "source" / "main.tex"
    command = [
        latexmk,
        # shell escape は明示的に無効化する(spec §15.4)
        "-lualatex=lualatex --no-shell-escape %O %S",
        "-halt-on-error",
        "-file-line-error",
        "-interaction=nonstopmode",
        f"-output-directory={out_dir}",
        str(main_tex),
    ]
    completed = subprocess.run(  # noqa: S603 -- 引数配列 + 解決済みバイナリで実行
        command,
        env=env,
        capture_output=True,
        text=True,
        check=False,
        timeout=_BUILD_TIMEOUT_SECONDS,
    )

    log_path = out_dir / "main.log"
    log_text = (
        log_path.read_text(encoding="utf-8", errors="replace")
        if log_path.is_file()
        else ""
    )
    missing, overfull = parse_latex_log(log_text)

    pdf_path = out_dir / "main.pdf"
    built = completed.returncode == 0 and pdf_path.is_file()
    # 欠損グリフはビルド失敗として扱う(spec §13.8)
    ok = built and not missing

    return TexBuildResult(
        material_id=manifest.id,
        template=template_dir,
        ok=ok,
        returncode=completed.returncode,
        pdf_path=str(pdf_path) if pdf_path.is_file() else None,
        log_path=str(log_path) if log_path.is_file() else None,
        missing_characters=missing,
        overfull_count=overfull,
        log_tail="" if ok else completed.stdout[-2000:],
    )
