"""Tests for structural material validation (spec §13.3 Stage C)."""

import json
import shutil
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from manabi_forge.cli.main import app
from manabi_forge.cli.material import EXIT_VALIDATION_FAILURE, discover_material_dirs
from manabi_forge.schema_export import find_repo_root
from manabi_forge.validation import IssueLevel, validate_material_dir

runner = CliRunner()

MATERIAL_ID = "math1-qf-guided-0001"

EXIT_USAGE_ERROR = 2  # spec §16.2: usage/configuration error


def make_manifest_data() -> dict:
    return {
        "schema_version": "1.0",
        "id": MATERIAL_ID,
        "version": "0.1.0",
        "title": "二次関数の最大・最小",
        "language": "ja",
        "status": "draft",
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
            "alignment_status": "pending",
        },
        "provenance": {
            "ai_assisted": True,
            "origin": "original",
            "source_text_included": False,
        },
    }


def make_provenance_data() -> dict:
    return {
        "schema_version": "1.0",
        "material_id": MATERIAL_ID,
        "authors": ["nishide-dev"],
        "similarity_review": "pending",
        "rights_review": "pending",
    }


@pytest.fixture
def material_dir(tmp_path) -> Path:
    """Create a structurally valid material directory in the standard layout."""
    directory = (
        tmp_path
        / "materials"
        / "mathematics"
        / "math-i"
        / "quadratic-functions"
        / MATERIAL_ID
    )
    (directory / "source").mkdir(parents=True)
    (directory / "source" / "main.tex").write_text(
        "\\documentclass[guided-example]{manabi}\n\\begin{document}x\\end{document}\n",
        encoding="utf-8",
    )
    (directory / "material.yaml").write_text(
        yaml.safe_dump(make_manifest_data(), allow_unicode=True),
        encoding="utf-8",
    )
    (directory / "provenance.yaml").write_text(
        yaml.safe_dump(make_provenance_data(), allow_unicode=True),
        encoding="utf-8",
    )
    (directory / "ATTRIBUTION.md").write_text(
        "# Attribution\n\nオリジナル教材。第三者素材なし。\n",
        encoding="utf-8",
    )
    return directory


def write_manifest(directory: Path, data: dict) -> None:
    (directory / "material.yaml").write_text(
        yaml.safe_dump(data, allow_unicode=True),
        encoding="utf-8",
    )


def errors_of(issues) -> set[str]:
    return {issue.code for issue in issues if issue.level is IssueLevel.ERROR}


class TestValidateMaterialDir:
    def test_valid_material_has_no_issues(self, material_dir):
        assert validate_material_dir(material_dir) == []

    def test_missing_directory(self, tmp_path):
        issues = validate_material_dir(tmp_path / "nope")
        assert errors_of(issues) == {"not-a-directory"}

    def test_missing_required_files(self, material_dir):
        (material_dir / "ATTRIBUTION.md").unlink()
        (material_dir / "provenance.yaml").unlink()
        assert errors_of(validate_material_dir(material_dir)) == {
            "missing-required-file",
        }

    def test_empty_source_dir(self, material_dir):
        (material_dir / "source" / "main.tex").unlink()
        assert "missing-source" in errors_of(validate_material_dir(material_dir))

    def test_malformed_manifest(self, material_dir):
        data = make_manifest_data()
        data["status"] = "not-a-status"
        write_manifest(material_dir, data)
        assert "manifest-schema-error" in errors_of(validate_material_dir(material_dir))

    def test_id_directory_mismatch(self, material_dir):
        data = make_manifest_data()
        data["id"] = "math1-qf-guided-0002"
        write_manifest(material_dir, data)
        codes = errors_of(validate_material_dir(material_dir))
        assert "id-path-mismatch" in codes

    def test_unit_not_in_units(self, material_dir):
        data = make_manifest_data()
        data["classification"]["units"] = ["equations-and-inequalities"]
        write_manifest(material_dir, data)
        assert "unit-path-mismatch" in errors_of(validate_material_dir(material_dir))

    def test_subject_path_mismatch(self, material_dir):
        data = make_manifest_data()
        data["classification"]["subject"] = "information"
        write_manifest(material_dir, data)
        assert "subject-path-mismatch" in errors_of(validate_material_dir(material_dir))

    def test_format_id_token_mismatch(self, material_dir):
        data = make_manifest_data()
        data["classification"]["format"] = "common-test-style"
        write_manifest(material_dir, data)
        codes = errors_of(validate_material_dir(material_dir))
        assert "format-id-mismatch" in codes

    def test_nonstandard_path_is_warning_only(self, tmp_path, material_dir):
        flat = tmp_path / MATERIAL_ID
        shutil.copytree(material_dir, flat)
        issues = validate_material_dir(flat)
        assert errors_of(issues) == set()
        assert any(issue.code == "nonstandard-path" for issue in issues)

    def test_provenance_id_mismatch(self, material_dir):
        data = make_provenance_data()
        data["material_id"] = "math1-qf-guided-0999"
        (material_dir / "provenance.yaml").write_text(
            yaml.safe_dump(data, allow_unicode=True),
            encoding="utf-8",
        )
        assert "provenance-id-mismatch" in errors_of(
            validate_material_dir(material_dir),
        )

    def test_placeholder_marker_detected(self, material_dir):
        (material_dir / "source" / "main.tex").write_text(
            "\\begin{document}TODO: 解答を書く\\end{document}\n",
            encoding="utf-8",
        )
        assert "placeholder-marker" in errors_of(validate_material_dir(material_dir))

    @pytest.mark.parametrize(
        "text",
        [
            "解答はTODOです",  # CJK 文字に挟まれたマーカー(\b では検出不能)
            "この問題のFIXMEを直す",
            "値はTBDとする",
            "ここにPLACEHOLDERを置く",
        ],
    )
    def test_placeholder_detected_inside_japanese_text(self, material_dir, text):
        (material_dir / "source" / "main.tex").write_text(
            f"\\begin{{document}}{text}\\end{{document}}\n",
            encoding="utf-8",
        )
        assert "placeholder-marker" in errors_of(validate_material_dir(material_dir))

    def test_placeholder_not_matched_inside_identifiers(self, material_dir):
        (material_dir / "source" / "main.tex").write_text(
            "\\begin{document}todo_list や mastodon は誤検出しない\\end{document}\n",
            encoding="utf-8",
        )
        assert "placeholder-marker" not in errors_of(
            validate_material_dir(material_dir),
        )

    def test_source_with_only_empty_subdir_is_missing(self, material_dir):
        (material_dir / "source" / "main.tex").unlink()
        (material_dir / "source" / "sub").mkdir()
        assert "missing-source" in errors_of(validate_material_dir(material_dir))

    def test_symlinked_material_dir_uses_resolved_path(self, tmp_path, material_dir):
        link = tmp_path / "link-to-material"
        link.symlink_to(material_dir, target_is_directory=True)
        issues = validate_material_dir(link)
        # 解決先は標準レイアウト内にあるため、警告なくエラーなしで検証される
        assert errors_of(issues) == set()
        assert not any(issue.code == "nonstandard-path" for issue in issues)

    def test_format_token_in_wrong_segment_is_rejected(self, material_dir):
        # course スロットに guided が入っていても format セグメントは common
        data = make_manifest_data()
        data["id"] = "guided-qf-common-0001"
        write_manifest(material_dir, data)
        renamed = material_dir.parent / "guided-qf-common-0001"
        material_dir.rename(renamed)
        prov = make_provenance_data()
        prov["material_id"] = "guided-qf-common-0001"
        (renamed / "provenance.yaml").write_text(
            yaml.safe_dump(prov, allow_unicode=True),
            encoding="utf-8",
        )
        assert "format-id-mismatch" in errors_of(validate_material_dir(renamed))

    def test_ai_common_test_requires_item_spec(self, material_dir):
        data = make_manifest_data()
        data["id"] = "math1-qf-common-0001"
        data["classification"]["format"] = "common-test-style"
        write_manifest(material_dir, data)
        renamed = material_dir.parent / "math1-qf-common-0001"
        material_dir.rename(renamed)
        prov = make_provenance_data()
        prov["material_id"] = "math1-qf-common-0001"
        (renamed / "provenance.yaml").write_text(
            yaml.safe_dump(prov, allow_unicode=True),
            encoding="utf-8",
        )
        assert "missing-item-spec" in errors_of(validate_material_dir(renamed))

    def test_item_id_mismatch(self, material_dir):
        (material_dir / "item.yaml").write_text(
            yaml.safe_dump(
                {
                    "material_id": "math1-qf-guided-0999",
                    "stem": "s",
                    "parts": [
                        {
                            "id": "a",
                            "prompt": "p",
                            "answer_type": "numeric",
                            "correct_answer": "1",
                        },
                    ],
                    "required_knowledge": ["k"],
                    "intended_reasoning": "r",
                    "solution_outline": "o",
                    "verification_strategy": "v",
                },
                allow_unicode=True,
            ),
            encoding="utf-8",
        )
        assert "item-id-mismatch" in errors_of(validate_material_dir(material_dir))

    def test_yaml_parse_error(self, material_dir):
        (material_dir / "material.yaml").write_text(
            "{{not yaml",
            encoding="utf-8",
        )
        assert "yaml-parse-error" in errors_of(validate_material_dir(material_dir))


class TestMaterialCli:
    def test_validate_ok(self, material_dir):
        result = runner.invoke(app, ["material", "validate", str(material_dir)])
        assert result.exit_code == 0
        assert "ok" in result.output

    def test_validate_failure_exit_code(self, material_dir):
        (material_dir / "ATTRIBUTION.md").unlink()
        result = runner.invoke(app, ["material", "validate", str(material_dir)])
        assert result.exit_code == EXIT_VALIDATION_FAILURE
        assert "missing-required-file" in result.output

    def test_validate_json_output(self, material_dir):
        result = runner.invoke(
            app,
            ["material", "validate", "--json", str(material_dir)],
        )
        payload = json.loads(result.output)
        assert payload["materials"][0]["issues"] == []

    def test_validate_json_output_reports_failure(self, material_dir):
        (material_dir / "ATTRIBUTION.md").unlink()
        result = runner.invoke(
            app,
            ["material", "validate", "--json", str(material_dir)],
        )
        assert result.exit_code == EXIT_VALIDATION_FAILURE
        payload = json.loads(result.output)
        codes = {issue["code"] for issue in payload["materials"][0]["issues"]}
        assert "missing-required-file" in codes

    def test_validate_multiple_targets_aggregates_errors(self, material_dir, tmp_path):
        broken = tmp_path / "broken" / MATERIAL_ID
        shutil.copytree(material_dir, broken)
        (broken / "ATTRIBUTION.md").unlink()
        result = runner.invoke(
            app,
            ["material", "validate", str(material_dir), str(broken)],
        )
        assert result.exit_code == EXIT_VALIDATION_FAILURE
        assert "1 errors" in result.output

    def test_discover_material_dirs(self, material_dir, tmp_path):
        found = discover_material_dirs(tmp_path / "materials")
        assert found == [material_dir]

    def test_missing_materials_root_is_usage_error(self, monkeypatch, tmp_path):
        # 既定走査対象が存在しない場合は検証成功(0)ではなく構成エラー(2)
        monkeypatch.setattr(
            "manabi_forge.cli.material.find_repo_root",
            lambda: tmp_path / "elsewhere",
        )
        result = runner.invoke(app, ["material", "validate"])
        assert result.exit_code == EXIT_USAGE_ERROR
        assert "materials root not found" in result.output

    def test_discover_skips_nested_material_yaml(self, material_dir, tmp_path):
        # 教材の source/ 配下の material.yaml(フィクスチャ等)は独立教材ではない
        (material_dir / "source" / "material.yaml").write_text(
            "id: fixture\n",
            encoding="utf-8",
        )
        found = discover_material_dirs(tmp_path / "materials")
        assert found == [material_dir]


def test_committed_repository_materials_are_valid():
    """リポジトリにコミット済みの全教材が構造的に妥当であること。"""
    materials_root = find_repo_root() / "materials"
    material_dirs = discover_material_dirs(materials_root)
    if not material_dirs:
        pytest.skip("no committed materials")
    for directory in material_dirs:
        issues = [
            issue
            for issue in validate_material_dir(directory)
            if issue.level is IssueLevel.ERROR
        ]
        assert issues == [], f"{directory}: {issues}"
