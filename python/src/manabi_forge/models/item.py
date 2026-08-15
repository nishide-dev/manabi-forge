"""ItemSpec model — semantic problem structure independent of TeX design (spec §11.4).

生成される共通テスト風アイテムには必須、個別問題には推奨。検索とレビューに
十分な構造を保ち、複雑な TeX は明示されたフィールドに限る。
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from manabi_forge.models.common import MaterialId, NonEmptyStr


class AnswerType(StrEnum):
    """How a part is answered."""

    MULTIPLE_CHOICE = "multiple-choice"
    NUMERIC = "numeric"
    EXPRESSION = "expression"
    SHORT_ANSWER = "short-answer"
    PROOF = "proof"


class Choice(BaseModel):
    """One answer choice, with distractor rationale where applicable."""

    model_config = ConfigDict(extra="forbid")

    label: NonEmptyStr
    text: NonEmptyStr
    is_correct: bool = False
    rationale: str = ""


class SourceData(BaseModel):
    """External source data used by the item, with license (spec §11.4, §20)."""

    model_config = ConfigDict(extra="forbid")

    description: NonEmptyStr
    license: NonEmptyStr
    url: str = ""
    attribution: str = ""


class Accessibility(BaseModel):
    """Accessibility descriptions for figures and data (spec §11.4, §17.7)."""

    model_config = ConfigDict(extra="forbid")

    figure_descriptions: list[NonEmptyStr] = Field(default_factory=list)


class ItemPart(BaseModel):
    """One part of a multi-part item."""

    model_config = ConfigDict(extra="forbid")

    id: NonEmptyStr
    prompt: NonEmptyStr
    answer_type: AnswerType
    correct_answer: NonEmptyStr
    choices: list[Choice] = Field(default_factory=list)

    @model_validator(mode="after")
    def _choices_match_answer_type(self) -> ItemPart:
        """Multiple-choice parts need choices with exactly one correct choice."""
        if self.answer_type is AnswerType.MULTIPLE_CHOICE:
            if len(self.choices) < 2:  # noqa: PLR2004 -- 選択式は最低 2 択
                msg = f"part {self.id}: multiple-choice requires at least 2 choices"
                raise ValueError(msg)
            correct = sum(1 for choice in self.choices if choice.is_correct)
            if correct != 1:
                msg = (
                    f"part {self.id}: expected exactly 1 correct choice, got {correct}"
                )
                raise ValueError(msg)
        elif self.choices:
            msg = f"part {self.id}: choices are only allowed for multiple-choice parts"
            raise ValueError(msg)
        return self


class ItemSpec(BaseModel):
    """Semantic structure of one problem (``item.yaml``, spec §11.4)."""

    model_config = ConfigDict(extra="forbid")

    schema_version: NonEmptyStr = "1.0"
    material_id: MaterialId
    stem: NonEmptyStr
    parts: list[ItemPart] = Field(min_length=1)

    required_knowledge: list[NonEmptyStr] = Field(min_length=1)
    intended_reasoning: NonEmptyStr
    solution_outline: NonEmptyStr
    verification_strategy: NonEmptyStr

    source_data: list[SourceData] = Field(default_factory=list)
    accessibility: Accessibility = Field(default_factory=Accessibility)

    @model_validator(mode="after")
    def _part_ids_unique(self) -> ItemSpec:
        """Part identifiers must be unique within one item."""
        ids = [part.id for part in self.parts]
        if len(ids) != len(set(ids)):
            msg = f"duplicate part ids: {sorted({i for i in ids if ids.count(i) > 1})}"
            raise ValueError(msg)
        return self
