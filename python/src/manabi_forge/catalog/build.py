"""Build the public ``catalog.json`` consumed by Manabi Library (spec §18.1).

catalog.json は公開可能なデータとリンクのみを含む。プロンプト、レビュアーの
連絡先、未公開教材、ローカルパスを含めてはならない。既定では approved /
published の教材のみを掲載する(spec §18.1)。開発プレビュー用に draft を
含めるオプションを持つが、公開デプロイでは使用しない。
"""

from __future__ import annotations

import json
from collections import Counter
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from manabi_forge.cli.material import discover_material_dirs
from manabi_forge.models import (
    CheckStatus,
    Difficulty,
    MaterialFormat,
    MaterialManifest,
    MaterialStatus,
)

if TYPE_CHECKING:
    from pathlib import Path

#: 既定で掲載する状態(spec §18.1: 承認済みの公開データのみ)。
PUBLIC_STATUSES: frozenset[MaterialStatus] = frozenset(
    {MaterialStatus.APPROVED, MaterialStatus.PUBLISHED},
)

CATALOG_SCHEMA_VERSION = "1.0"


class CatalogBuildError(ValueError):
    """Raised when the materials tree cannot produce a valid public catalog."""


class CatalogArtifacts(BaseModel):
    """Public artifact links (release assets), never local paths."""

    model_config = ConfigDict(extra="forbid")

    problem_pdf: str | None = None
    answer_sheet_pdf: str | None = None
    solution_pdf: str | None = None
    source_bundle: str | None = None

    @field_validator("*")
    @classmethod
    def _public_https_url(cls, value: str | None) -> str | None:
        """Reject anything but credential-free https URLs (spec §18.1).

        マニフェスト由来の自由文字列がカタログへ素通りする唯一の経路なので、
        ローカルパスや資格情報付き URL はここで遮断する。
        """
        if value is None:
            return value
        parsed = urlsplit(value)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username:
            msg = f"artifact link must be a credential-free https URL, got {value!r}"
            raise ValueError(msg)
        return value


class CatalogEntry(BaseModel):
    """One public catalog row (mirrors ``web/src/lib/catalog.ts``)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    version: str
    title: str
    language: str
    status: MaterialStatus
    subject: str
    course: str
    units: list[str]
    format: MaterialFormat
    difficulty: Difficulty
    estimated_minutes: int
    curriculum_snapshot: str
    curriculum_codes: list[str]
    validation: dict[str, CheckStatus]
    license: str
    ai_assisted: bool
    artifacts: CatalogArtifacts


class CatalogFile(BaseModel):
    """Top-level catalog document."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = CATALOG_SCHEMA_VERSION
    includes_drafts: bool = False
    materials: list[CatalogEntry] = Field(default_factory=list)


def _entry_from_manifest(manifest: MaterialManifest) -> CatalogEntry:
    """Project the public subset of one manifest into a catalog entry."""
    return CatalogEntry(
        id=manifest.id,
        version=manifest.version,
        title=manifest.title,
        language=manifest.language,
        status=manifest.status,
        subject=manifest.classification.subject,
        course=manifest.classification.course,
        units=list(manifest.classification.units),
        format=manifest.classification.format,
        difficulty=manifest.classification.difficulty,
        estimated_minutes=manifest.classification.estimated_minutes,
        curriculum_snapshot=manifest.curriculum.snapshot,
        curriculum_codes=list(manifest.curriculum.codes),
        validation=manifest.validation.model_dump(by_alias=True),
        license=manifest.license.content,
        ai_assisted=manifest.provenance.ai_assisted,
        artifacts=CatalogArtifacts.model_validate(
            manifest.artifacts.model_dump(),
        ),
    )


def build_catalog(
    materials_root: Path,
    *,
    include_drafts: bool = False,
) -> CatalogFile:
    """Build the catalog from every material manifest under ``materials_root``."""
    entries: list[CatalogEntry] = []
    for material_dir in discover_material_dirs(materials_root):
        manifest_path = material_dir / "material.yaml"
        try:
            manifest = MaterialManifest.model_validate(
                yaml.safe_load(manifest_path.read_text(encoding="utf-8")),
            )
            if not include_drafts and manifest.status not in PUBLIC_STATUSES:
                continue
            entries.append(_entry_from_manifest(manifest))
        except (ValidationError, yaml.YAMLError) as exc:
            # どの教材が原因か分かるようパスを添えて失敗させる
            msg = f"{manifest_path}: {exc}"
            raise CatalogBuildError(msg) from exc

    duplicates = sorted(
        material_id
        for material_id, count in Counter(entry.id for entry in entries).items()
        if count > 1
    )
    if duplicates:
        # 重複 ID は Web 側で片方が到達不能になるため許容しない
        msg = f"duplicate material ids: {duplicates}"
        raise CatalogBuildError(msg)

    entries.sort(key=lambda entry: entry.id)
    return CatalogFile(includes_drafts=include_drafts, materials=entries)


def render_catalog_json(catalog: CatalogFile) -> str:
    """Render the catalog as deterministic JSON text."""
    payload = catalog.model_dump(mode="json")
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
