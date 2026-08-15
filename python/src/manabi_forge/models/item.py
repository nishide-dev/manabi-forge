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


class VerificationKind(StrEnum):
    """Machine-checkable verification strategies (spec §13.4)."""

    MAXIMUM = "maximum"
    MINIMUM = "minimum"
    VERTEX = "vertex"
    EQUIVALENT = "equivalent"


class VerificationCheck(BaseModel):
    """One machine-checkable claim about the item (spec §13.4).

    expression は変数 x の SymPy 可読な式。domain は閉区間 [a, b]、
    None は実数全体を表す。ここに載らない主張は自動検証の対象外として
    人間レビューへ明示的にエスカレートされる。
    """

    model_config = ConfigDict(extra="forbid")

    id: NonEmptyStr
    kind: VerificationKind
    expression: NonEmptyStr
    domain: tuple[float, float] | None = None
    expected_x: float | None = None
    expected_value: float | None = None
    rhs: str | None = None

    @model_validator(mode="after")
    def _fields_match_kind(self) -> VerificationCheck:
        """Require the fields each verification kind needs."""
        needs_extrema = self.kind in {
            VerificationKind.MAXIMUM,
            VerificationKind.MINIMUM,
            VerificationKind.VERTEX,
        }
        if needs_extrema and (self.expected_x is None or self.expected_value is None):
            msg = f"check {self.id}: {self.kind.value} requires expected_x and expected_value"
            raise ValueError(msg)
        if self.kind is VerificationKind.EQUIVALENT and not self.rhs:
            msg = f"check {self.id}: equivalent requires rhs"
            raise ValueError(msg)
        if self.domain is not None and self.domain[0] >= self.domain[1]:
            msg = f"check {self.id}: domain must satisfy a < b"
            raise ValueError(msg)
        return self


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
        """Enforce choice consistency for multiple-choice parts.

        選択肢ラベルの重複と、``correct_answer`` と ``is_correct`` の
        二重表現の食い違い(spec §11.5 の non-unique-answer 系欠陥)を拒否する。
        """
        if self.answer_type is AnswerType.MULTIPLE_CHOICE:
            if len(self.choices) < 2:  # noqa: PLR2004 -- 選択式は最低 2 択
                msg = f"part {self.id}: multiple-choice requires at least 2 choices"
                raise ValueError(msg)
            labels = [choice.label for choice in self.choices]
            if len(labels) != len(set(labels)):
                msg = f"part {self.id}: choice labels must be unique"
                raise ValueError(msg)
            correct_labels = [c.label for c in self.choices if c.is_correct]
            if len(correct_labels) != 1:
                msg = (
                    f"part {self.id}: expected exactly 1 correct choice, "
                    f"got {len(correct_labels)}"
                )
                raise ValueError(msg)
            if self.correct_answer != correct_labels[0]:
                msg = (
                    f"part {self.id}: correct_answer {self.correct_answer!r} does not "
                    f"match the correct choice label {correct_labels[0]!r}"
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
    verification_checks: list[VerificationCheck] = Field(default_factory=list)

    @model_validator(mode="after")
    def _part_ids_unique(self) -> ItemSpec:
        """Part identifiers must be unique within one item."""
        ids = [part.id for part in self.parts]
        if len(ids) != len(set(ids)):
            msg = f"duplicate part ids: {sorted({i for i in ids if ids.count(i) > 1})}"
            raise ValueError(msg)
        return self
