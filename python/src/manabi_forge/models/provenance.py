"""Provenance record model — who and what produced a material (spec §11.6).

プロンプト原文や資格情報は保存しない。要約またはハッシュのみを記録する。
"""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from manabi_forge.models.common import CheckStatus, MaterialId, NonEmptyStr, Sha256

PromptSummary = Annotated[str, StringConstraints(max_length=500)]
"""プロンプトの要約。長大な文字列はプロンプト原文の混入とみなして拒否する。"""


class AiStep(BaseModel):
    """One AI-assisted step.

    プロンプト原文や資格情報は保存しない(spec §11.6)。ハッシュは SHA-256、
    要約は 500 文字以内に制約し、原文の丸ごと貼り付けを型レベルで防ぐ。
    """

    model_config = ConfigDict(extra="forbid")

    description: NonEmptyStr
    model: str = ""
    prompt_hash: Sha256 | None = None
    prompt_summary: PromptSummary = ""


class SourceRef(BaseModel):
    """One source dataset or document with its license."""

    model_config = ConfigDict(extra="forbid")

    description: NonEmptyStr
    license: NonEmptyStr
    url: str = ""


class ProvenanceRecord(BaseModel):
    """Full provenance of a material (``provenance.yaml``, spec §11.6)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: NonEmptyStr = "1.0"
    material_id: MaterialId

    authors: list[NonEmptyStr] = Field(
        min_length=1,
        description="人間の著者。編集責任のため最低 1 名(spec §20.5)。",
    )
    editors: list[NonEmptyStr] = Field(default_factory=list)
    ai_steps: list[AiStep] = Field(default_factory=list)
    sources: list[SourceRef] = Field(default_factory=list)

    similarity_review: CheckStatus = CheckStatus.PENDING
    rights_review: CheckStatus = CheckStatus.PENDING
