"""Structural validation of a material directory (spec §13.3 Stage C).

決定論的なチェックのみを行う。数学的検証(Stage D)や各種レビュー
(Stage E-H)はここでは行わず、それぞれの仕組みに委ねる。
"""

from __future__ import annotations

import re
from enum import StrEnum
from typing import TYPE_CHECKING

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError

from manabi_forge.models import (
    ItemSpec,
    MaterialFormat,
    MaterialManifest,
    ProvenanceRecord,
)

if TYPE_CHECKING:
    from pathlib import Path


class IssueLevel(StrEnum):
    """Severity of a structural validation issue."""

    ERROR = "error"
    WARNING = "warning"


class ValidationIssue(BaseModel):
    """One structural validation issue."""

    model_config = ConfigDict(extra="forbid")

    level: IssueLevel
    code: str
    location: str
    message: str


REQUIRED_FILES = ("material.yaml", "provenance.yaml", "ATTRIBUTION.md")

#: プレースホルダー・禁止マーカー(spec §13.3)。禁止フレーズ(商用シリーズ名
#: など)は権利レビュー導入時に追加する。
#: 注意: CJK 文字は \w に含まれ日本語文中ではマーカー前後に \b が発生しない
#: ため、\b ではなく ASCII 英数のみを除外する明示的な lookaround を使う。
PLACEHOLDER_PATTERN = re.compile(
    r"(?<![0-9A-Za-z_])(TODO|FIXME|TBD|PLACEHOLDER|CHANGEME|lorem ipsum)(?![0-9A-Za-z_])",
    re.IGNORECASE,
)

#: format と教材 ID 中のセグメントの対応(spec §11.2 の例に基づく)。
FORMAT_ID_TOKENS: dict[MaterialFormat, str] = {
    MaterialFormat.COMMON_TEST_STYLE: "common",
    MaterialFormat.GUIDED_EXAMPLE: "guided",
    MaterialFormat.WORKSHEET: "worksheet",
}

#: プレースホルダー走査の対象拡張子。
SCAN_SUFFIXES = frozenset({".tex", ".yaml", ".yml", ".md"})

#: materials/<subject>/<course>/<unit>/<id> 標準レイアウトの深さ。
_MATERIALS_ANCESTOR_DEPTH = 4


def _error(code: str, location: str, message: str) -> ValidationIssue:
    return ValidationIssue(
        level=IssueLevel.ERROR,
        code=code,
        location=location,
        message=message,
    )


def _warning(code: str, location: str, message: str) -> ValidationIssue:
    return ValidationIssue(
        level=IssueLevel.WARNING,
        code=code,
        location=location,
        message=message,
    )


def _load_yaml(path: Path) -> tuple[object | None, ValidationIssue | None]:
    """Load a YAML file, returning the data or a parse issue."""
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return None, _error("yaml-parse-error", path.name, f"YAML の解析に失敗: {exc}")
    except OSError as exc:
        return None, _error("file-unreadable", path.name, f"読み込みに失敗: {exc}")
    return data, None


def _summarize_validation_error(exc: ValidationError) -> str:
    """Convert a Pydantic error into a compact one-line summary."""
    parts = [
        f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}"
        for err in exc.errors()
    ]
    return "; ".join(parts)


def _check_required_files(material_dir: Path) -> list[ValidationIssue]:
    issues = [
        _error("missing-required-file", name, "必須ファイルが存在しない")
        for name in REQUIRED_FILES
        if not (material_dir / name).is_file()
    ]
    source_dir = material_dir / "source"
    if not source_dir.is_dir() or not any(
        path.is_file() for path in source_dir.rglob("*")
    ):
        issues.append(
            _error("missing-source", "source/", "source/ にファイルが存在しない"),
        )
    return issues


def _check_manifest(
    material_dir: Path,
) -> tuple[MaterialManifest | None, list[ValidationIssue]]:
    path = material_dir / "material.yaml"
    if not path.is_file():
        return None, []  # missing-required-file として既に報告済み
    data, issue = _load_yaml(path)
    if issue is not None:
        return None, [issue]
    try:
        manifest = MaterialManifest.model_validate(data)
    except ValidationError as exc:
        return None, [
            _error(
                "manifest-schema-error",
                "material.yaml",
                _summarize_validation_error(exc),
            ),
        ]
    return manifest, []


def _check_path_consistency(
    material_dir: Path,
    manifest: MaterialManifest,
) -> list[ValidationIssue]:
    """Check ID/directory agreement and the standard materials layout.

    ID チェックとレイアウトチェックは同じ解決済みパスを基準にする
    (シンボリックリンク経由で両者の基準がずれることを防ぐ)。
    """
    issues: list[ValidationIssue] = []
    resolved = material_dir.resolve()
    if resolved.name != manifest.id:
        issues.append(
            _error(
                "id-path-mismatch",
                "material.yaml:id",
                f"ディレクトリ名 {resolved.name!r} と id {manifest.id!r} が一致しない",
            ),
        )

    ancestors = list(resolved.parents)
    if (
        len(ancestors) >= _MATERIALS_ANCESTOR_DEPTH
        and ancestors[_MATERIALS_ANCESTOR_DEPTH - 1].name == "materials"
    ):
        unit_dir, course_dir, subject_dir = (
            resolved.parent.name,
            ancestors[1].name,
            ancestors[2].name,
        )
        del course_dir  # course ディレクトリは省略名(例: math-i)のため照合しない
        if subject_dir != manifest.classification.subject:
            issues.append(
                _error(
                    "subject-path-mismatch",
                    "material.yaml:classification.subject",
                    f"subject ディレクトリ {subject_dir!r} と "
                    f"classification.subject {manifest.classification.subject!r} "
                    "が一致しない",
                ),
            )
        if unit_dir not in manifest.classification.units:
            issues.append(
                _error(
                    "unit-path-mismatch",
                    "material.yaml:classification.units",
                    f"unit ディレクトリ {unit_dir!r} が units に含まれていない",
                ),
            )
    else:
        issues.append(
            _warning(
                "nonstandard-path",
                str(material_dir),
                "materials/<subject>/<course>/<unit>/<id> 標準レイアウト外のため"
                "パス整合チェックを省略した",
            ),
        )
    return issues


def _check_format_id_token(manifest: MaterialManifest) -> list[ValidationIssue]:
    """Check the format segment of the ID (spec §11.2).

    format は ``<course>-<unit>-<format>-<serial>`` の連番直前に位置するため、
    末尾から 2 番目のセグメントを照合する(任意位置の一致では別スロットの
    トークンで擦り抜けられる)。
    """
    token = FORMAT_ID_TOKENS[manifest.classification.format]
    segments = manifest.id.split("-")
    format_segment = segments[-2] if len(segments) >= 2 else ""  # noqa: PLR2004
    if format_segment != token:
        return [
            _error(
                "format-id-mismatch",
                "material.yaml:classification.format",
                f"id {manifest.id!r} の format セグメント {format_segment!r} が "
                f"format {manifest.classification.format.value!r} に対応する "
                f"{token!r} と一致しない",
            ),
        ]
    return []


def _check_provenance(
    material_dir: Path,
    manifest: MaterialManifest,
) -> list[ValidationIssue]:
    path = material_dir / "provenance.yaml"
    if not path.is_file():
        return []  # missing-required-file として既に報告済み
    data, issue = _load_yaml(path)
    if issue is not None:
        return [issue]
    try:
        record = ProvenanceRecord.model_validate(data)
    except ValidationError as exc:
        return [
            _error(
                "provenance-schema-error",
                "provenance.yaml",
                _summarize_validation_error(exc),
            ),
        ]
    if record.material_id != manifest.id:
        return [
            _error(
                "provenance-id-mismatch",
                "provenance.yaml:material_id",
                f"material_id {record.material_id!r} が id {manifest.id!r} と一致しない",
            ),
        ]
    return []


def _check_item_spec(
    material_dir: Path,
    manifest: MaterialManifest,
) -> list[ValidationIssue]:
    """Validate item.yaml; 生成された共通テスト風教材には必須(spec §11.4)."""
    path = material_dir / "item.yaml"
    required = (
        manifest.classification.format is MaterialFormat.COMMON_TEST_STYLE
        and manifest.provenance.ai_assisted
    )
    if not path.is_file():
        if required:
            return [
                _error(
                    "missing-item-spec",
                    "item.yaml",
                    "AI 支援の共通テスト風教材には item.yaml が必須",
                ),
            ]
        return []
    data, issue = _load_yaml(path)
    if issue is not None:
        return [issue]
    try:
        item = ItemSpec.model_validate(data)
    except ValidationError as exc:
        return [
            _error(
                "item-schema-error",
                "item.yaml",
                _summarize_validation_error(exc),
            ),
        ]
    if item.material_id != manifest.id:
        return [
            _error(
                "item-id-mismatch",
                "item.yaml:material_id",
                f"material_id {item.material_id!r} が id {manifest.id!r} と一致しない",
            ),
        ]
    return []


def _check_placeholders(material_dir: Path) -> list[ValidationIssue]:
    """Scan text sources for placeholder markers (spec §13.3)."""
    issues: list[ValidationIssue] = []
    for path in sorted(material_dir.rglob("*")):
        if not path.is_file() or path.suffix not in SCAN_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            issues.append(
                _error(
                    "file-unreadable",
                    str(path.relative_to(material_dir)),
                    f"読み込みに失敗: {exc}",
                ),
            )
            continue
        match = PLACEHOLDER_PATTERN.search(text)
        if match:
            issues.append(
                _error(
                    "placeholder-marker",
                    str(path.relative_to(material_dir)),
                    f"プレースホルダー {match.group(0)!r} が残っている",
                ),
            )
    return issues


def validate_material_dir(material_dir: Path) -> list[ValidationIssue]:
    """Run every structural check on one material directory."""
    if not material_dir.is_dir():
        return [
            _error(
                "not-a-directory",
                str(material_dir),
                "教材ディレクトリが存在しない",
            ),
        ]

    issues = _check_required_files(material_dir)
    manifest, manifest_issues = _check_manifest(material_dir)
    issues.extend(manifest_issues)
    if manifest is not None:
        issues.extend(_check_path_consistency(material_dir, manifest))
        issues.extend(_check_format_id_token(manifest))
        issues.extend(_check_provenance(material_dir, manifest))
        issues.extend(_check_item_spec(material_dir, manifest))
    issues.extend(_check_placeholders(material_dir))
    return issues
