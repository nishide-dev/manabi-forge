"""Tests for TeX building (spec §9.5, §15)."""

import os
import shutil
import subprocess
from pathlib import Path
from typing import NoReturn

import pytest
import yaml

from manabi_forge.cli.material import discover_material_dirs
from manabi_forge.schema_export import find_repo_root
from manabi_forge.tex import (
    LatexmkNotFoundError,
    build_material,
    parse_latex_log,
)
from manabi_forge.tex.build import _texinputs

HAS_TEX = shutil.which("latexmk") is not None and shutil.which("lualatex") is not None


class TestParseLatexLog:
    def test_extracts_missing_characters(self):
        log = (
            "Missing character: There is no あ in font cmr10!\n"
            "Missing character: There is no あ in font cmr10!\n"
        )
        missing, overfull = parse_latex_log(log)
        assert len(missing) == 1
        assert "cmr10" in missing[0]
        assert overfull == 0

    def test_counts_overfull_boxes(self):
        log = (
            "Overfull \\hbox (10.0pt too wide) in paragraph\n"
            "some text\n"
            "Overfull \\vbox (3.0pt too high) detected\n"
        )
        missing, overfull = parse_latex_log(log)
        assert missing == []
        assert overfull == 2

    def test_counts_overfull_boxes_with_prefixes(self):
        # -file-line-error のプレフィックスやインデントが付いても数える
        log = (
            "./main.tex:5: Overfull \\hbox (1.0pt too wide)\n"
            " Overfull \\vbox (2.0pt too high)\n"
        )
        _missing, overfull = parse_latex_log(log)
        assert overfull == 2

    def test_empty_log(self):
        assert parse_latex_log("") == ([], 0)


class TestTexinputs:
    def test_prepends_shared_and_template_dirs(self, tmp_path):
        value = _texinputs(tmp_path, "guided-example", {})
        parts = value.split(os.pathsep)
        assert parts[0].endswith("shared")
        assert parts[1].endswith("guided-example")
        assert parts[-1] == ""  # 既定検索パスを維持する空要素

    def test_preserves_existing_texinputs(self, tmp_path):
        value = _texinputs(tmp_path, "worksheet", {"TEXINPUTS": "/custom:"})
        assert value.endswith("/custom:")

    def test_appends_separator_when_existing_has_none(self, tmp_path):
        # 既定検索パスを表す末尾の空要素が必ず残ること(欠けると
        # article.cls すら見つからなくなる)
        value = _texinputs(tmp_path, "worksheet", {"TEXINPUTS": "/custom"})
        assert value.endswith("/custom" + os.pathsep)


def test_build_raises_without_latexmk(monkeypatch, tmp_path):
    monkeypatch.setattr("manabi_forge.tex.build.shutil.which", lambda _name: None)
    with pytest.raises(LatexmkNotFoundError):
        build_material(tmp_path)


def make_plain_material(tmp_path, body: str) -> Path:
    """Create a minimal buildable material with the given TeX body."""
    directory = tmp_path / "math1-qf-guided-0001"
    (directory / "source").mkdir(parents=True)
    (directory / "material.yaml").write_text(
        yaml.safe_dump(
            {
                "id": "math1-qf-guided-0001",
                "version": "0.1.0",
                "title": "テスト",
                "classification": {
                    "subject": "mathematics",
                    "course": "mathematics-i",
                    "units": ["quadratic-functions"],
                    "format": "guided-example",
                    "difficulty": "standard",
                    "estimated_minutes": 5,
                },
                "curriculum": {
                    "snapshot": "test",
                    "codes": ["84V10-math-i-quadratic-functions"],
                },
                "provenance": {"ai_assisted": False},
            },
            allow_unicode=True,
        ),
        encoding="utf-8",
    )
    (directory / "source" / "main.tex").write_text(
        f"\\documentclass{{article}}\n\\begin{{document}}\n{body}\n\\end{{document}}\n",
        encoding="utf-8",
    )
    return directory


def test_build_timeout_returns_failed_result(monkeypatch, tmp_path):
    def raise_timeout(*_args: object, **_kwargs: object) -> NoReturn:
        raise subprocess.TimeoutExpired(cmd="latexmk", timeout=1, output=b"partial")

    material = make_plain_material(tmp_path, "x")
    monkeypatch.setattr("manabi_forge.tex.build.subprocess.run", raise_timeout)
    result = build_material(material, out_root=tmp_path / "build")
    assert not result.ok
    assert result.returncode == -1
    assert "timed out" in result.log_tail


@pytest.mark.skipif(not HAS_TEX, reason="TeX Live (latexmk + lualatex) not installed")
def test_failed_build_reports_not_ok_without_stale_pdf(tmp_path):
    material = make_plain_material(tmp_path, "\\thiscommanddoesnotexist")
    result = build_material(material, out_root=tmp_path / "build")
    assert not result.ok
    assert result.returncode != 0
    assert result.pdf_path is None  # 失敗時に PDF を指さない


@pytest.mark.skipif(not HAS_TEX, reason="TeX Live (latexmk + lualatex) not installed")
def test_missing_glyph_fails_the_build(tmp_path):
    # article + 既定フォント(Latin Modern)には日本語グリフがない(spec §13.8)
    material = make_plain_material(tmp_path, "あ")
    result = build_material(material, out_root=tmp_path / "build")
    assert not result.ok
    assert result.missing_characters


@pytest.mark.skipif(not HAS_TEX, reason="TeX Live (latexmk + lualatex) not installed")
def test_build_committed_sample_material(tmp_path):
    """コミット済みサンプル教材が実際に PDF までビルドできること(spec §13.8)。"""
    root = find_repo_root()
    materials = discover_material_dirs(root / "materials")
    if not materials:
        pytest.skip("no committed materials")
    result = build_material(materials[0], out_root=tmp_path)
    assert result.ok, result.log_tail
    assert result.pdf_path is not None
    assert result.missing_characters == []
