"""Release manifest model — generated JSON attached to release assets (spec §18, Appendix B).

Appendix B の例に合わせて JSON 表現は camelCase を用いる(YAML 正本は snake_case)。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from manabi_forge.models.common import (
    CheckStatus,
    GitSha,
    MaterialId,
    NonEmptyStr,
    SemVer,
    Sha256,
)


class TemplateRef(BaseModel):
    """Template identity and version recorded in every artifact (spec §15.3)."""

    model_config = ConfigDict(
        extra="forbid", alias_generator=to_camel, populate_by_name=True
    )

    id: NonEmptyStr
    version: SemVer


class ReleaseArtifact(BaseModel):
    """One published artifact with its checksum (spec §18.2)."""

    model_config = ConfigDict(
        extra="forbid", alias_generator=to_camel, populate_by_name=True
    )

    kind: NonEmptyStr
    filename: NonEmptyStr
    sha256: Sha256


class ReleaseManifest(BaseModel):
    """Manifest describing one immutable material release (spec §18, Appendix B)."""

    model_config = ConfigDict(
        extra="forbid", alias_generator=to_camel, populate_by_name=True
    )

    material_id: MaterialId
    material_version: SemVer
    source_commit: GitSha
    curriculum_snapshot: NonEmptyStr
    template: TemplateRef
    reviews: dict[str, CheckStatus] = Field(
        description="レビュー種別ごとの結果。公開には全必須レビューの passed が必要。",
    )
    artifacts: list[ReleaseArtifact] = Field(min_length=1)
