"""Prepare immutable release assets for one material (spec §18).

必須レビューが欠けている・不合格の教材のリリースは拒否する(spec §12.3,
§13.9)。生成物: 命名済み PDF、ソースバンドル ZIP、リリースマニフェスト
(Appendix B、camelCase)、SHA256SUMS。公開済みアセットは不変であり、
修正は新バージョンとして発行する(ADR-005)。
"""

from __future__ import annotations

import hashlib
import json
import re
import zipfile
from typing import TYPE_CHECKING

import yaml
from pydantic import BaseModel, ConfigDict, Field

from manabi_forge.models import (
    CheckStatus,
    MaterialManifest,
    MaterialStatus,
    ReleaseManifest,
    ReviewType,
)
from manabi_forge.schema_export import find_repo_root
from manabi_forge.tex.build import TEMPLATE_DIRS, build_material

if TYPE_CHECKING:
    from pathlib import Path

#: リリース可能な教材状態(spec §11.1, §13.9)。
RELEASABLE_STATUSES = frozenset({MaterialStatus.APPROVED, MaterialStatus.PUBLISHED})

#: ソースバンドルに含める教材ディレクトリ内のエントリ(spec §18.3)。
_BUNDLE_ENTRIES = (
    "material.yaml",
    "item.yaml",
    "provenance.yaml",
    "ATTRIBUTION.md",
    "README.md",
    "source",
    "assets",
    "reviews",
)

_PROVIDES_VERSION = re.compile(r"\[\d{4}/\d{2}/\d{2} v([0-9.]+)")


class ReleaseBlockedError(RuntimeError):
    """Raised when a material does not meet the release gate."""


class ReleaseResult(BaseModel):
    """Paths of the prepared release assets."""

    model_config = ConfigDict(extra="forbid")

    material_id: str
    version: str
    tag: str
    assets: list[str] = Field(default_factory=list)


def _require_releasable(manifest: MaterialManifest) -> None:
    """Refuse release when reviews are missing or not passed (spec §13.9)."""
    if manifest.status not in RELEASABLE_STATUSES:
        msg = (
            f"{manifest.id}: status {manifest.status.value!r} is not releasable "
            "(approved or published required; ADR-004)"
        )
        raise ReleaseBlockedError(msg)
    validation = manifest.validation.model_dump(by_alias=True)
    not_passed = sorted(
        name for name, status in validation.items() if status is not CheckStatus.PASSED
    )
    if not_passed:
        msg = f"{manifest.id}: validation not passed for {not_passed}"
        raise ReleaseBlockedError(msg)


def _template_version(repo_root: Path, template_dir: str) -> str:
    r"""Read the template version from its ``\ProvidesPackage`` line (spec §15.3)."""
    sty = repo_root / "templates" / template_dir / f"manabi-{template_dir}.sty"
    match = _PROVIDES_VERSION.search(sty.read_text(encoding="utf-8"))
    if match is None:
        msg = f"cannot determine template version from {sty}"
        raise ReleaseBlockedError(msg)
    return match.group(1)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_source_bundle(
    material_dir: Path,
    repo_root: Path,
    out_path: Path,
    *,
    template_dir: str,
    template_version: str,
) -> None:
    """Create the source ZIP (spec §18.3): 教材ソース + ライセンス + ビルド手順."""
    build_notes = (
        "# Build instructions\n\n"
        "リポジトリルートで以下を実行すると PDF を再現できます:\n\n"
        "```bash\n"
        "cd python && uv sync --locked && \\\n"
        f"  uv run manabi tex build ../materials/.../{material_dir.name}\n"
        "```\n\n"
        f"テンプレート: {template_dir} v{template_version}(templates/ 配下)。\n"
        "エンジン: LuaLaTeX + latexmk(shell escape 無効)。\n"
    )
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as bundle:
        for entry in _BUNDLE_ENTRIES:
            source = material_dir / entry
            if source.is_file():
                bundle.write(source, f"{material_dir.name}/{entry}")
            elif source.is_dir():
                for path in sorted(source.rglob("*")):
                    if path.is_file():
                        bundle.write(
                            path,
                            f"{material_dir.name}/{path.relative_to(material_dir)}",
                        )
        for template_path in sorted(
            (repo_root / "templates" / "shared").glob("*"),
        ) + sorted((repo_root / "templates" / template_dir).glob("*")):
            if template_path.is_file():
                bundle.write(
                    template_path,
                    f"templates/{template_path.relative_to(repo_root / 'templates')}",
                )
        bundle.write(repo_root / "LICENSE-CONTENT", "LICENSE-CONTENT")
        bundle.write(repo_root / "LICENSE-CODE", "LICENSE-CODE")
        bundle.writestr(f"{material_dir.name}/BUILD.md", build_notes)


def prepare_release(
    material_dir: Path,
    *,
    source_commit: str,
    repo_root: Path | None = None,
    out_root: Path | None = None,
) -> ReleaseResult:
    """Build and stage every release asset for one approved material."""
    root = repo_root if repo_root is not None else find_repo_root()
    manifest = MaterialManifest.model_validate(
        yaml.safe_load((material_dir / "material.yaml").read_text(encoding="utf-8")),
    )
    _require_releasable(manifest)

    build = build_material(material_dir, repo_root=root)
    if not build.ok or build.pdf_path is None:
        msg = f"{manifest.id}: TeX build failed; cannot release"
        raise ReleaseBlockedError(msg)

    template_dir = TEMPLATE_DIRS[manifest.classification.format]
    template_version = _template_version(root, template_dir)

    stem = f"{manifest.id}-v{manifest.version}"
    out_dir = (out_root if out_root is not None else root / "build" / "release") / stem
    out_dir.mkdir(parents=True, exist_ok=True)

    problem_pdf = out_dir / f"{stem}-problem.pdf"
    problem_pdf.write_bytes((root / build.pdf_path).read_bytes())

    source_zip = out_dir / f"{stem}-source.zip"
    _write_source_bundle(
        material_dir,
        root,
        source_zip,
        template_dir=template_dir,
        template_version=template_version,
    )

    release_manifest = ReleaseManifest.model_validate(
        {
            "material_id": manifest.id,
            "material_version": manifest.version,
            "source_commit": source_commit,
            "curriculum_snapshot": manifest.curriculum.snapshot,
            "template": {"id": template_dir, "version": template_version},
            "reviews": dict.fromkeys(ReviewType, CheckStatus.PASSED),
            "artifacts": [
                {
                    "kind": "problem-pdf",
                    "filename": problem_pdf.name,
                    "sha256": _sha256(problem_pdf),
                },
                {
                    "kind": "source-bundle",
                    "filename": source_zip.name,
                    "sha256": _sha256(source_zip),
                },
            ],
        },
    )
    manifest_path = out_dir / f"{stem}-manifest.json"
    manifest_path.write_text(
        json.dumps(
            release_manifest.model_dump(mode="json", by_alias=True),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    sums_path = out_dir / f"{stem}-SHA256SUMS"
    sums_path.write_text(
        "".join(
            f"{_sha256(path)}  {path.name}\n"
            for path in (problem_pdf, source_zip, manifest_path)
        ),
        encoding="utf-8",
    )

    return ReleaseResult(
        material_id=manifest.id,
        version=manifest.version,
        tag=stem,
        assets=[str(p) for p in (problem_pdf, source_zip, manifest_path, sums_path)],
    )
