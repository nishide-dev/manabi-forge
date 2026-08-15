"""Tests for JSON Schema export (spec §9.3)."""

import json

import pytest

from manabi_forge.models import MaterialManifest
from manabi_forge.schema_export import (
    JSON_SCHEMA_DIALECT,
    SCHEMA_EXPORTS,
    RepoRootNotFoundError,
    check_schemas,
    find_repo_root,
    render_schema,
    write_schemas,
)


def test_render_schema_is_deterministic_json():
    first = render_schema(MaterialManifest, "material.schema.json")
    second = render_schema(MaterialManifest, "material.schema.json")
    assert first == second
    parsed = json.loads(first)
    assert parsed["$schema"] == JSON_SCHEMA_DIALECT
    assert parsed["$id"].endswith("/schemas/material.schema.json")


def test_write_then_check_round_trip(tmp_path):
    written = write_schemas(tmp_path)
    assert {path.name for path in written} == set(SCHEMA_EXPORTS)
    assert check_schemas(tmp_path) == []


def test_check_detects_stale_schema(tmp_path):
    write_schemas(tmp_path)
    (tmp_path / "material.schema.json").write_text("{}\n", encoding="utf-8")
    assert check_schemas(tmp_path) == ["material.schema.json"]


def test_check_detects_missing_schema(tmp_path):
    write_schemas(tmp_path)
    (tmp_path / "item.schema.json").unlink()
    assert "item.schema.json" in check_schemas(tmp_path)


def test_find_repo_root_locates_git_directory(tmp_path):
    (tmp_path / ".git").mkdir()
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    assert find_repo_root(nested) == tmp_path


def test_find_repo_root_raises_when_no_git_anywhere(monkeypatch, tmp_path):
    # 実行環境の祖先ディレクトリに .git があっても影響を受けないよう、
    # 存在チェック自体を常に偽にする。
    monkeypatch.setattr("manabi_forge.schema_export.Path.exists", lambda _self: False)
    with pytest.raises(RepoRootNotFoundError):
        find_repo_root(tmp_path)
