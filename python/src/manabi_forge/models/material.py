"""Material manifest model — the canonical ``material.yaml`` structure (spec §11.3)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, PositiveInt

from manabi_forge.models.common import (
    AlignmentStatus,
    CheckStatus,
    Difficulty,
    MaterialFormat,
    MaterialId,
    MaterialStatus,
    NonEmptyStr,
    SemVer,
)


class Classification(BaseModel):
    """Catalog classification of a material (spec §11.3, §17.2)."""

    model_config = ConfigDict(extra="forbid")

    school_level: NonEmptyStr = "high-school"
    subject: NonEmptyStr
    course: NonEmptyStr
    units: list[NonEmptyStr] = Field(min_length=1)
    format: MaterialFormat
    difficulty: Difficulty
    estimated_minutes: PositiveInt
    audience: list[NonEmptyStr] = Field(default_factory=lambda: ["learner"])


class CurriculumAlignment(BaseModel):
    """Curriculum snapshot and codes a material cites (spec §10, §11.3)."""

    model_config = ConfigDict(extra="forbid")

    snapshot: NonEmptyStr
    codes: list[NonEmptyStr] = Field(min_length=1)
    alignment_status: AlignmentStatus = AlignmentStatus.PENDING


class Artifacts(BaseModel):
    """Release artifact references. PDF はリポジトリではなくリリースアセット(ADR-005)."""

    model_config = ConfigDict(extra="forbid")

    problem_pdf: str | None = None
    answer_sheet_pdf: str | None = None
    solution_pdf: str | None = None
    source_bundle: str | None = None


class ValidationState(BaseModel):
    """Per-dimension validation and review state (spec §11.3, §13)."""

    model_config = ConfigDict(extra="forbid")

    schema_check: CheckStatus = Field(default=CheckStatus.PENDING, alias="schema")
    tex: CheckStatus = CheckStatus.PENDING
    mathematics: CheckStatus = CheckStatus.PENDING
    curriculum: CheckStatus = CheckStatus.PENDING
    editorial: CheckStatus = CheckStatus.PENDING
    visual: CheckStatus = CheckStatus.PENDING
    rights: CheckStatus = CheckStatus.PENDING


class LicenseInfo(BaseModel):
    """License split: content = CC BY 4.0, code = Apache-2.0 (spec §20.1)."""

    model_config = ConfigDict(extra="forbid")

    content: NonEmptyStr = "CC-BY-4.0"
    code: NonEmptyStr = "Apache-2.0"


class ProvenanceSummary(BaseModel):
    """Provenance flags surfaced in the manifest; details live in provenance.yaml."""

    model_config = ConfigDict(extra="forbid")

    ai_assisted: bool
    origin: NonEmptyStr = "original"
    source_text_included: bool = False


class MaterialManifest(BaseModel):
    """Canonical material manifest (``material.yaml``, spec §11.3).

    正本は PDF ではなくこのマニフェストと TeX ソース・レビュー/来歴レコード
    である(spec §6.2)。
    """

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    schema_version: NonEmptyStr = "1.0"
    id: MaterialId
    version: SemVer
    title: NonEmptyStr
    language: NonEmptyStr = "ja"
    status: MaterialStatus = MaterialStatus.DRAFT

    classification: Classification
    curriculum: CurriculumAlignment
    artifacts: Artifacts = Field(default_factory=Artifacts)
    validation: ValidationState = Field(default_factory=ValidationState)
    license: LicenseInfo = Field(default_factory=LicenseInfo)
    provenance: ProvenanceSummary
