"""Tests for release preparation (spec §18)."""

import json
import shutil
import zipfile
from pathlib import Path

import pytest
import yaml

from manabi_forge.cli.material import discover_material_dirs
from manabi_forge.release import ReleaseBlockedError, prepare_release
from manabi_forge.schema_export import find_repo_root

HAS_TEX = shutil.which("latexmk") is not None and shutil.which("lualatex") is not None

COMMIT = "0123456789abcdef0123456789abcdef01234567"


def repo_material() -> Path:
    root = find_repo_root()
    return discover_material_dirs(root / "materials")[0]


def test_release_blocked_for_unapproved_material(tmp_path):
    source = repo_material()
    clone = tmp_path / source.name
    shutil.copytree(source, clone)
    manifest_path = clone / "material.yaml"
    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    data["status"] = "draft"
    manifest_path.write_text(
        yaml.safe_dump(data, allow_unicode=True),
        encoding="utf-8",
    )
    with pytest.raises(ReleaseBlockedError, match="not releasable"):
        prepare_release(clone, source_commit=COMMIT, out_root=tmp_path / "out")


def test_release_blocked_when_validation_not_passed(tmp_path):
    source = repo_material()
    clone = tmp_path / source.name
    shutil.copytree(source, clone)
    manifest_path = clone / "material.yaml"
    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    data["validation"]["rights"] = "pending"
    manifest_path.write_text(
        yaml.safe_dump(data, allow_unicode=True),
        encoding="utf-8",
    )
    with pytest.raises(ReleaseBlockedError, match="rights"):
        prepare_release(clone, source_commit=COMMIT, out_root=tmp_path / "out")


@pytest.mark.skipif(not HAS_TEX, reason="TeX Live (latexmk + lualatex) not installed")
def test_prepare_release_produces_complete_asset_set(tmp_path):
    """spec §18.2 のアセット一式(PDF / source.zip / manifest / SHA256SUMS)。"""
    material = repo_material()
    result = prepare_release(material, source_commit=COMMIT, out_root=tmp_path)
    names = {Path(asset).name for asset in result.assets}
    stem = result.tag
    assert names == {
        f"{stem}-problem.pdf",
        f"{stem}-source.zip",
        f"{stem}-manifest.json",
        f"{stem}-SHA256SUMS",
    }

    manifest = json.loads(
        (tmp_path / stem / f"{stem}-manifest.json").read_text(encoding="utf-8"),
    )
    # Appendix B: camelCase、全レビュー passed、チェックサム付き
    assert manifest["materialId"] == result.material_id
    assert manifest["sourceCommit"] == COMMIT
    assert set(manifest["reviews"]) == {
        "mathematics",
        "curriculum",
        "editorial",
        "visual",
        "rights",
    }
    assert all(status == "passed" for status in manifest["reviews"].values())
    assert len(manifest["artifacts"]) == 2

    sums = (tmp_path / stem / f"{stem}-SHA256SUMS").read_text(encoding="utf-8")
    assert f"{stem}-problem.pdf" in sums
    assert f"{stem}-source.zip" in sums

    with zipfile.ZipFile(tmp_path / stem / f"{stem}-source.zip") as bundle:
        entries = set(bundle.namelist())
    material_id = result.material_id
    assert f"{material_id}/material.yaml" in entries
    assert f"{material_id}/source/main.tex" in entries
    assert f"{material_id}/BUILD.md" in entries
    assert "LICENSE-CONTENT" in entries
    assert any(name.startswith("templates/shared/") for name in entries)
    # 秘匿情報・ビルドキャッシュを含めない(spec §18.3)
    assert not any(".venv" in name or "build/" in name for name in entries)
