"""Normalized curriculum record model (spec §10.3).

公式資料そのものではなく、出典参照付きの正規化レコード。official text と
maintainer 解釈は source_refs と review.status で区別できる形を保つ。
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from manabi_forge.models.common import NonEmptyStr


class ObjectiveDimension(StrEnum):
    """学習指導要領の資質・能力の三つの柱."""

    KNOWLEDGE_AND_SKILLS = "knowledge-and-skills"
    THINKING_JUDGMENT_EXPRESSION = "thinking-judgment-expression"
    ATTITUDE_TOWARD_LEARNING = "attitude-toward-learning"


class CurriculumReviewStatus(StrEnum):
    """Human review state of one normalized record (spec §10.4-10.5)."""

    PENDING = "pending"
    REVIEWED = "reviewed"


class CurriculumSourceRef(BaseModel):
    """Reference into an official source document (evidence, spec §10.6)."""

    model_config = ConfigDict(extra="forbid")

    id: NonEmptyStr
    locator: NonEmptyStr


class CurriculumReview(BaseModel):
    """Who reviewed this normalized record against the official text."""

    model_config = ConfigDict(extra="forbid")

    status: CurriculumReviewStatus = CurriculumReviewStatus.PENDING
    reviewed_by: str = ""
    reviewed_at: date | None = None


class CurriculumRecord(BaseModel):
    """One normalized curriculum record (spec §10.3).

    statement_ja は maintainer による要約であり、公式文書の複製ではない。
    正確な文言は source_refs の出典を参照する。
    """

    model_config = ConfigDict(extra="forbid")

    code: NonEmptyStr
    source_version: NonEmptyStr
    school_level: NonEmptyStr
    subject: NonEmptyStr
    course: NonEmptyStr
    path: list[NonEmptyStr] = Field(min_length=1)
    statement_ja: NonEmptyStr
    objective_dimensions: list[ObjectiveDimension] = Field(min_length=1)
    prerequisites: list[NonEmptyStr] = Field(default_factory=list)
    scope_notes: list[NonEmptyStr] = Field(default_factory=list)
    restrictions: list[NonEmptyStr] = Field(default_factory=list)
    source_refs: list[CurriculumSourceRef] = Field(min_length=1)
    uncertainty_notes: list[NonEmptyStr] = Field(default_factory=list)
    review: CurriculumReview = Field(default_factory=CurriculumReview)
