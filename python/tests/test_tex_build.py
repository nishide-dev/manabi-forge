"""Tests for TeX building (spec §9.5, §15)."""

import os
import shutil

import pytest

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


def test_build_raises_without_latexmk(monkeypatch, tmp_path):
    monkeypatch.setattr("manabi_forge.tex.build.shutil.which", lambda _name: None)
    with pytest.raises(LatexmkNotFoundError):
        build_material(tmp_path)


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
