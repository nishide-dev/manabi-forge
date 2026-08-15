"""Pydantic data models — the Python source of truth for Manabi Forge data.

これらのモデルから JSON Schema Draft 2020-12 を生成して `schemas/` にコミットする
(spec §9.3)。スキーマファイルを手書きで編集してはならない。
"""

from manabi_forge.models.common import (
    AlignmentStatus,
    CheckStatus,
    Difficulty,
    MaterialFormat,
    MaterialStatus,
    ReviewerKind,
    ReviewResult,
    ReviewType,
    Severity,
)
from manabi_forge.models.item import ItemPart, ItemSpec
from manabi_forge.models.material import MaterialManifest
from manabi_forge.models.provenance import ProvenanceRecord
from manabi_forge.models.release import ReleaseManifest
from manabi_forge.models.review import Finding, Reviewer, ReviewRecord

__all__ = [
    "AlignmentStatus",
    "CheckStatus",
    "Difficulty",
    "Finding",
    "ItemPart",
    "ItemSpec",
    "MaterialFormat",
    "MaterialManifest",
    "MaterialStatus",
    "ProvenanceRecord",
    "ReleaseManifest",
    "ReviewRecord",
    "ReviewResult",
    "ReviewType",
    "Reviewer",
    "ReviewerKind",
    "Severity",
]
