"""Tests for the public catalog builder (spec §18.1)."""

import json
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from manabi_forge.catalog import (
    CatalogBuildError,
    CatalogEntry,
    build_catalog,
    render_catalog_json,
)
from manabi_forge.cli.main import app

runner = CliRunner()

#: 許可リストが破れたときに必ず検出されるよう、漏れてはならない値を
#: あえて含んだ敵対的なマニフェストを使う。
SECRET_MARKERS = (
    "reviewer@example.com",
    "SECRET-PROMPT-BODY",
    "/home/alice/private",
)


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
            # audience は許可リスト外であり出力に現れてはならない
            "audience": ["learner", SECRET_MARKERS[0]],
        },
        "curriculum": {
            "snapshot": "mext-84V10-2026-08",
            "codes": ["84V10-math-i-quadratic-functions"],
        },
        "provenance": {
            "ai_assisted": True,
            "origin": SECRET_MARKERS[1],
            "source_text_included": False,
        },
    }


def write_material(
    root: Path,
    material_id: str,
    status: str,
    *,
    manifest: dict | None = None,
) -> Path:
    directory = root / "mathematics" / "math-i" / "quadratic-functions" / material_id
    (directory / "source").mkdir(parents=True)
    (directory / "material.yaml").write_text(
        yaml.safe_dump(
            manifest if manifest is not None else make_manifest(material_id, status),
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    return directory


class TestBuildCatalog:
    def test_excludes_unapproved_materials_by_default(self, tmp_path):
        for serial, status in enumerate(
            ["draft", "generated", "under-review", "changes-requested", "deprecated"],
            start=1,
        ):
            write_material(tmp_path, f"math1-qf-guided-{serial:04d}", status)
        write_material(tmp_path, "math1-qf-guided-0101", "approved")
        write_material(tmp_path, "math1-qf-guided-0102", "published")
        catalog = build_catalog(tmp_path)
        assert [entry.id for entry in catalog.materials] == [
            "math1-qf-guided-0101",
            "math1-qf-guided-0102",
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

    def test_entry_fields_are_exactly_the_public_allowlist(self):
        # 許可リストの拡張は必ずこのテストの更新(= 意図的なレビュー)を伴う
        assert set(CatalogEntry.model_fields) == {
            "id",
            "version",
            "title",
            "language",
            "status",
            "subject",
            "course",
            "units",
            "format",
            "difficulty",
            "estimated_minutes",
            "curriculum_snapshot",
            "curriculum_codes",
            "validation",
            "license",
            "ai_assisted",
            "artifacts",
        }

    def test_output_contains_no_private_data(self, tmp_path):
        write_material(tmp_path, "math1-qf-guided-0001", "approved")
        text = render_catalog_json(build_catalog(tmp_path))
        assert str(tmp_path) not in text
        for marker in SECRET_MARKERS:
            assert marker not in text

    def test_rejects_local_path_artifacts(self, tmp_path):
        manifest = make_manifest("math1-qf-guided-0001", "approved")
        manifest["artifacts"] = {"problem_pdf": SECRET_MARKERS[2] + "/p.pdf"}
        write_material(tmp_path, "math1-qf-guided-0001", "approved", manifest=manifest)
        with pytest.raises(CatalogBuildError, match="https URL"):
            build_catalog(tmp_path)

    def test_rejects_artifact_urls_with_credentials(self, tmp_path):
        manifest = make_manifest("math1-qf-guided-0001", "approved")
        manifest["artifacts"] = {"problem_pdf": "https://user:token@host/p.pdf"}
        write_material(tmp_path, "math1-qf-guided-0001", "approved", manifest=manifest)
        with pytest.raises(CatalogBuildError, match="credential-free"):
            build_catalog(tmp_path)

    def test_accepts_plain_https_artifact_urls(self, tmp_path):
        manifest = make_manifest("math1-qf-guided-0001", "approved")
        url = "https://github.com/nishide-dev/manabi-forge/releases/download/v1/p.pdf"
        manifest["artifacts"] = {"problem_pdf": url}
        write_material(tmp_path, "math1-qf-guided-0001", "approved", manifest=manifest)
        entry = build_catalog(tmp_path).materials[0]
        assert entry.artifacts.problem_pdf == url

    def test_rejects_duplicate_material_ids(self, tmp_path):
        first = write_material(tmp_path, "math1-qf-guided-0001", "approved")
        del first
        other_unit = tmp_path / "mathematics" / "math-i" / "other-unit"
        manifest = make_manifest("math1-qf-guided-0001", "approved")
        directory = other_unit / "math1-qf-guided-0001"
        (directory / "source").mkdir(parents=True)
        (directory / "material.yaml").write_text(
            yaml.safe_dump(manifest, allow_unicode=True),
            encoding="utf-8",
        )
        with pytest.raises(CatalogBuildError, match="duplicate material ids"):
            build_catalog(tmp_path)

    def test_unreadable_manifest_names_the_file(self, tmp_path):
        directory = write_material(tmp_path, "math1-qf-guided-0001", "approved")
        (directory / "material.yaml").write_text("id: [broken", encoding="utf-8")
        with pytest.raises(CatalogBuildError, match=r"material\.yaml"):
            build_catalog(tmp_path)

    def test_render_is_deterministic(self, tmp_path):
        write_material(tmp_path, "math1-qf-guided-0001", "approved")
        first = render_catalog_json(build_catalog(tmp_path))
        second = render_catalog_json(build_catalog(tmp_path))
        assert first == second
        assert json.loads(first)["schema_version"] == "1.0"


class TestCatalogCli:
    @pytest.fixture
    def materials_root(self, tmp_path) -> Path:
        root = tmp_path / "materials"
        write_material(root, "math1-qf-guided-0001", "draft")
        write_material(root, "math1-qf-guided-0002", "approved")
        return root

    def test_build_writes_catalog_json(self, materials_root, tmp_path):
        out = tmp_path / "out" / "catalog.json"
        result = runner.invoke(
            app,
            [
                "catalog",
                "build",
                "--include-drafts",
                "--materials-root",
                str(materials_root),
                "--out",
                str(out),
            ],
        )
        assert result.exit_code == 0
        payload = json.loads(out.read_text(encoding="utf-8"))
        assert [m["id"] for m in payload["materials"]] == [
            "math1-qf-guided-0001",
            "math1-qf-guided-0002",
        ]
        assert "do not deploy" in result.output

    def test_build_default_excludes_drafts(self, materials_root, tmp_path):
        out = tmp_path / "catalog.json"
        result = runner.invoke(
            app,
            [
                "catalog",
                "build",
                "--materials-root",
                str(materials_root),
                "--out",
                str(out),
            ],
        )
        assert result.exit_code == 0
        payload = json.loads(out.read_text(encoding="utf-8"))
        assert [m["id"] for m in payload["materials"]] == ["math1-qf-guided-0002"]

    def test_build_fails_on_broken_manifest(self, materials_root, tmp_path):
        (
            materials_root
            / "mathematics"
            / "math-i"
            / "quadratic-functions"
            / "math1-qf-guided-0001"
            / "material.yaml"
        ).write_text("id: [broken", encoding="utf-8")
        result = runner.invoke(
            app,
            [
                "catalog",
                "build",
                "--materials-root",
                str(materials_root),
                "--out",
                str(tmp_path / "c.json"),
            ],
        )
        assert result.exit_code == 1

    def test_missing_materials_root_is_usage_error(self, tmp_path):
        result = runner.invoke(
            app,
            [
                "catalog",
                "build",
                "--materials-root",
                str(tmp_path / "nope"),
                "--out",
                str(tmp_path / "c.json"),
            ],
        )
        assert result.exit_code == 2
