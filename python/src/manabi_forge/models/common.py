"""Shared types and enumerations for Manabi Forge data models (spec §11, §14)."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import StringConstraints

MATERIAL_ID_PATTERN = r"^[a-z0-9]+(-[a-z0-9]+)*-\d{4}$"
"""教材 ID 形式 ``<course>-<unit>-<format>-<serial>``(spec §11.2)。

course / unit / format の各セグメントは複数語(ハイフン区切り)でもよいため、
パターンは「小文字英数セグメント列 + 4 桁連番」のみを保証する。セグメントの
意味的な整合(例: format と classification.format の一致)はディレクトリ構造を
参照できる教材バリデーション(issue #2)で検査する。
"""

SEMVER_PATTERN = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$"

GIT_SHA_PATTERN = r"^[0-9a-f]{7,40}$"

SHA256_PATTERN = r"^[0-9a-f]{64}$"

MaterialId = Annotated[str, StringConstraints(pattern=MATERIAL_ID_PATTERN)]

SemVer = Annotated[str, StringConstraints(pattern=SEMVER_PATTERN)]

GitSha = Annotated[str, StringConstraints(pattern=GIT_SHA_PATTERN)]

Sha256 = Annotated[str, StringConstraints(pattern=SHA256_PATTERN)]

NonEmptyStr = Annotated[str, StringConstraints(min_length=1)]


class MaterialStatus(StrEnum):
    """Material lifecycle states (spec §11.1)."""

    DRAFT = "draft"
    GENERATED = "generated"
    STRUCTURALLY_VALID = "structurally-valid"
    UNDER_REVIEW = "under-review"
    CHANGES_REQUESTED = "changes-requested"
    APPROVED = "approved"
    PUBLISHED = "published"
    REVISED = "revised"
    DEPRECATED = "deprecated"


class MaterialFormat(StrEnum):
    """Publication formats. 商用シリーズ名は使用しない(spec §4.4)."""

    COMMON_TEST_STYLE = "common-test-style"
    GUIDED_EXAMPLE = "guided-example"
    WORKSHEET = "worksheet"


class Difficulty(StrEnum):
    """Coarse difficulty scale for catalog filtering (spec §17.2)."""

    BASIC = "basic"
    STANDARD = "standard"
    ADVANCED = "advanced"


class CheckStatus(StrEnum):
    """State of one validation or review dimension (spec §11.3)."""

    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"


class AlignmentStatus(StrEnum):
    """Curriculum alignment state of a material (spec §10.5, §11.3)."""

    PENDING = "pending"
    ALIGNED = "aligned"
    NEEDS_CURRICULUM_REVIEW = "needs-curriculum-review"


class ReviewType(StrEnum):
    """Review specialties recorded as separate review records (spec §13)."""

    MATHEMATICS = "mathematics"
    CURRICULUM = "curriculum"
    EDITORIAL = "editorial"
    VISUAL = "visual"
    RIGHTS = "rights"


class ReviewResult(StrEnum):
    """Outcome of a single review (spec §11.5, Appendix C)."""

    PASSED = "passed"
    CHANGES_REQUESTED = "changes-requested"
    ESCALATED = "escalated"


class ReviewerKind(StrEnum):
    """Who performed a review. 自動レビューは人間レビューと偽装しない(spec §11.5)."""

    HUMAN = "human"
    AUTOMATED = "automated"


class Severity(StrEnum):
    """Finding severity levels and their publication effect (spec §14.1)."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NOTE = "note"
