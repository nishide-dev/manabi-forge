"""Load and query normalized curriculum records (spec §10.3, §10.6).

`curriculum/normalized/` 配下の YAML(1 ファイル = 1 レコード)を読み込む。
リゾルバは真偽値ではなく、根拠(レコード)と不確実性ノートを返す。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from manabi_forge.models.curriculum import CurriculumRecord

if TYPE_CHECKING:
    from pathlib import Path


class DuplicateCodeError(ValueError):
    """Raised when two normalized records share the same curriculum code."""


class InvalidRecordError(ValueError):
    """Raised when a normalized record file fails schema validation."""


class CurriculumStore(BaseModel):
    """In-memory index of normalized curriculum records."""

    model_config = ConfigDict(extra="forbid")

    records: list[CurriculumRecord] = Field(default_factory=list)

    def by_code(self, code: str) -> CurriculumRecord | None:
        """Return the record for ``code``, or ``None``."""
        return next((r for r in self.records if r.code == code), None)

    def missing_codes(self, codes: list[str]) -> list[str]:
        """Return the subset of ``codes`` that resolve to no record."""
        known = {record.code for record in self.records}
        return [code for code in codes if code not in known]

    def query(
        self,
        *,
        course: str | None = None,
        unit: str | None = None,
        text: str | None = None,
    ) -> list[CurriculumRecord]:
        """Filter records by course, unit (path segment), and free text."""
        results = self.records
        if course is not None:
            results = [r for r in results if r.course == course]
        if unit is not None:
            results = [r for r in results if unit in r.path]
        if text is not None:
            needle = text.casefold()
            results = [
                r
                for r in results
                if needle in r.statement_ja.casefold()
                or any(needle in note.casefold() for note in r.scope_notes)
            ]
        return results


def load_store(normalized_dir: Path) -> CurriculumStore:
    """Load every normalized record under ``normalized_dir``.

    重複コードは取り込み事故のサインなので即座に失敗させる。
    """
    records: list[CurriculumRecord] = []
    seen: dict[str, Path] = {}
    paths = sorted(
        path
        for pattern in ("*.yaml", "*.yml")
        for path in normalized_dir.rglob(pattern)
    )
    for path in paths:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        try:
            record = CurriculumRecord.model_validate(data)
        except ValidationError as exc:
            # どのファイルが壊れているか分かるよう、パスを添えて再送出する
            msg = f"invalid curriculum record {path}: {exc}"
            raise InvalidRecordError(msg) from exc
        if record.code in seen:
            msg = f"duplicate curriculum code {record.code!r}: {seen[record.code]} and {path}"
            raise DuplicateCodeError(msg)
        seen[record.code] = path
        records.append(record)
    return CurriculumStore(records=records)
