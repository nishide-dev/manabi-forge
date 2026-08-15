"""Tests for the curriculum knowledge base (spec §10)."""

from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from manabi_forge.cli.main import app
from manabi_forge.curriculum import CurriculumStore, DuplicateCodeError, load_store
from manabi_forge.models.curriculum import CurriculumRecord
from manabi_forge.schema_export import find_repo_root

runner = CliRunner()


def make_record_data(code: str = "84V10-test-0001") -> dict:
    return {
        "code": code,
        "source_version": "84V10",
        "school_level": "high-school",
        "subject": "mathematics",
        "course": "mathematics-i",
        "path": ["quadratic-functions"],
        "statement_ja": "テスト用の要約。",
        "objective_dimensions": ["knowledge-and-skills"],
        "source_refs": [
            {"id": "mext-course-of-study-2018-math", "locator": "数学I 2内容 (3)"},
        ],
    }


def write_record(directory: Path, data: dict) -> Path:
    path = directory / f"{data['code']}.yaml"
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    return path


class TestCurriculumRecord:
    def test_accepts_valid_record(self):
        record = CurriculumRecord.model_validate(make_record_data())
        assert record.review.status.value == "pending"

    def test_requires_source_refs(self):
        data = make_record_data()
        data["source_refs"] = []
        with pytest.raises(ValueError, match="source_refs"):
            CurriculumRecord.model_validate(data)


class TestLoadStore:
    def test_loads_records_recursively(self, tmp_path):
        nested = tmp_path / "mathematics-i" / "quadratic-functions"
        nested.mkdir(parents=True)
        write_record(nested, make_record_data("84V10-a-0001"))
        write_record(nested, make_record_data("84V10-b-0001"))
        store = load_store(tmp_path)
        assert len(store.records) == 2

    def test_rejects_duplicate_codes(self, tmp_path):
        (tmp_path / "a").mkdir()
        (tmp_path / "b").mkdir()
        write_record(tmp_path / "a", make_record_data("84V10-dup-0001"))
        write_record(tmp_path / "b", make_record_data("84V10-dup-0001"))
        with pytest.raises(DuplicateCodeError):
            load_store(tmp_path)


class TestStoreQueries:
    @pytest.fixture
    def store(self) -> CurriculumStore:
        first = make_record_data("84V10-a-0001")
        second = make_record_data("84V10-b-0001")
        second["course"] = "mathematics-a"
        second["path"] = ["probability"]
        second["statement_ja"] = "場合の数と確率を扱う。"
        return CurriculumStore(
            records=[
                CurriculumRecord.model_validate(first),
                CurriculumRecord.model_validate(second),
            ],
        )

    def test_missing_codes(self, store):
        missing = store.missing_codes(["84V10-a-0001", "84V10-nope-0001"])
        assert missing == ["84V10-nope-0001"]

    def test_query_by_course_and_unit(self, store):
        assert len(store.query(course="mathematics-i")) == 1
        assert len(store.query(unit="probability")) == 1
        assert store.query(course="mathematics-i", unit="probability") == []

    def test_query_by_text(self, store):
        assert len(store.query(text="確率")) == 1


class TestRepositoryData:
    def test_committed_records_load_and_are_unique(self):
        normalized = find_repo_root() / "curriculum" / "normalized"
        store = load_store(normalized)
        assert len(store.records) >= 1

    def test_committed_materials_codes_resolve(self):
        """全教材の curriculum codes が正規レコードに解決できること。"""
        root = find_repo_root()
        store = load_store(root / "curriculum" / "normalized")
        manifests = sorted((root / "materials").rglob("material.yaml"))
        assert manifests, "committed materials expected"
        for manifest_path in manifests:
            data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
            missing = store.missing_codes(data["curriculum"]["codes"])
            assert missing == [], f"{manifest_path}: unresolved {missing}"


class TestCurriculumCli:
    def test_validate_passes_on_repository(self):
        result = runner.invoke(app, ["curriculum", "validate"])
        assert result.exit_code == 0
        assert "curriculum records loaded" in result.output

    def test_query_by_unit(self):
        result = runner.invoke(
            app,
            ["curriculum", "query", "--unit", "quadratic-functions"],
        )
        assert result.exit_code == 0
        assert "84V10-math-i-quadratic-functions" in result.output

    def test_query_json(self):
        result = runner.invoke(
            app,
            ["curriculum", "query", "--course", "mathematics-i", "--json"],
        )
        assert result.exit_code == 0
        assert '"code"' in result.output
