"""Tests for the public catalog builder (spec §18.1)."""

import json
from pathlib import Path

import yaml
from typer.testing import CliRunner

from manabi_forge.catalog import build_catalog, render_catalog_json
from manabi_forge.cli.main import app

runner = CliRunner()


def make_manifest(material_id: str, status: str) -> dict:
    return {
        "schema_version": "1.0",
        "id": material_id,
        "version": "0.1.0",
        "title": "二次関数の最大・最小",
        "language": "ja",
        "status": status,
        "classification": {
            "school_level": "high-school",
            "subject": "mathematics",
            "course": "mathematics-i",
            "units": ["quadratic-functions"],
            "format": "guided-example",
            "difficulty": "standard",
            "estimated_minutes": 15,
            "audience": ["learner"],
        },
        "curriculum": {
            "snapshot": "mext-84V10-2026-08",
            "codes": ["84V10-math-i-quadratic-functions"],
        },
        "provenance": {
            "ai_assisted": True,
            "origin": "original",
            "source_text_included": False,
        },
    }


def write_material(root: Path, material_id: str, status: str) -> Path:
    directory = root / "mathematics" / "math-i" / "quadratic-functions" / material_id
    (directory / "source").mkdir(parents=True)
    (directory / "material.yaml").write_text(
        yaml.safe_dump(make_manifest(material_id, status), allow_unicode=True),
        encoding="utf-8",
    )
    return directory


class TestBuildCatalog:
    def test_excludes_unapproved_materials_by_default(self, tmp_path):
        write_material(tmp_path, "math1-qf-guided-0001", "draft")
        write_material(tmp_path, "math1-qf-guided-0002", "approved")
        write_material(tmp_path, "math1-qf-guided-0003", "published")
        catalog = build_catalog(tmp_path)
        assert [entry.id for entry in catalog.materials] == [
            "math1-qf-guided-0002",
            "math1-qf-guided-0003",
        ]
        assert not catalog.includes_drafts

    def test_include_drafts_flag(self, tmp_path):
        write_material(tmp_path, "math1-qf-guided-0001", "draft")
        catalog = build_catalog(tmp_path, include_drafts=True)
        assert len(catalog.materials) == 1
        assert catalog.includes_drafts

    def test_entry_projects_public_fields(self, tmp_path):
        write_material(tmp_path, "math1-qf-guided-0001", "approved")
        entry = build_catalog(tmp_path).materials[0]
        assert entry.license == "CC-BY-4.0"
        assert entry.ai_assisted is True
        assert entry.validation["schema"] == "pending"
        assert entry.artifacts.problem_pdf is None

    def test_output_contains_no_private_data(self, tmp_path):
        write_material(tmp_path, "math1-qf-guided-0001", "approved")
        text = render_catalog_json(build_catalog(tmp_path))
        # ローカルパス・プロンプト・メールアドレスを含めない(spec §18.1)
        assert str(tmp_path) not in text
        assert "prompt" not in text
        assert "@" not in text

    def test_render_is_deterministic(self, tmp_path):
        write_material(tmp_path, "math1-qf-guided-0001", "approved")
        first = render_catalog_json(build_catalog(tmp_path))
        second = render_catalog_json(build_catalog(tmp_path))
        assert first == second
        assert json.loads(first)["schema_version"] == "1.0"


class TestCatalogCli:
    def test_build_writes_catalog_json(self, tmp_path):
        result = runner.invoke(
            app,
            ["catalog", "build", "--include-drafts", "--out", str(tmp_path / "c.json")],
        )
        assert result.exit_code == 0
        payload = json.loads((tmp_path / "c.json").read_text(encoding="utf-8"))
        # リポジトリの draft サンプル教材が含まれる
        ids = [m["id"] for m in payload["materials"]]
        assert "math1-qf-guided-0001" in ids
        assert "do not deploy" in result.output

    def test_build_default_excludes_repo_drafts(self, tmp_path):
        result = runner.invoke(
            app,
            ["catalog", "build", "--out", str(tmp_path / "c.json")],
        )
        assert result.exit_code == 0
        payload = json.loads((tmp_path / "c.json").read_text(encoding="utf-8"))
        assert payload["materials"] == []
