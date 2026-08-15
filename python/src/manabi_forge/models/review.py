"""Review record model — immutable review files under ``reviews/`` (spec §11.5)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from manabi_forge.models.common import (
    GitSha,
    MaterialId,
    NonEmptyStr,
    ReviewerKind,
    ReviewResult,
    ReviewType,
    Severity,
)


class Reviewer(BaseModel):
    """Who performed the review.

    自動レビューはツール名とバージョンを識別し、人間レビューと偽装しない
    (spec §11.5)。
    """

    model_config = ConfigDict(extra="forbid")

    kind: ReviewerKind
    name: NonEmptyStr
    tool_version: str = ""

    @model_validator(mode="after")
    def _automated_requires_tool_version(self) -> Reviewer:
        """Automated reviewers must identify the tool version."""
        if self.kind is ReviewerKind.AUTOMATED and not self.tool_version:
            msg = "automated reviewer must set tool_version"
            raise ValueError(msg)
        return self


class Finding(BaseModel):
    """One structured review finding (spec §11.5, severities in §14.1)."""

    model_config = ConfigDict(extra="forbid")

    severity: Severity
    location: NonEmptyStr
    code: NonEmptyStr
    message: NonEmptyStr
    suggested_action: str = ""


class ReviewRecord(BaseModel):
    """One immutable review of a material at a specific commit (spec §11.5).

    正式レビュー中に教材を書き換えてはならない。指摘はこのレコードとして残す。
    """

    model_config = ConfigDict(extra="forbid")

    schema_version: NonEmptyStr = "1.0"
    material_id: MaterialId
    review_id: NonEmptyStr
    review_type: ReviewType
    reviewer: Reviewer
    reviewed_commit: GitSha
    result: ReviewResult
    findings: list[Finding] = Field(default_factory=list)
    created_at: datetime

    @model_validator(mode="after")
    def _changes_requested_needs_findings(self) -> ReviewRecord:
        """Require at least one finding when changes are requested."""
        if self.result is ReviewResult.CHANGES_REQUESTED and not self.findings:
            msg = "changes-requested review must include at least one finding"
            raise ValueError(msg)
        return self
