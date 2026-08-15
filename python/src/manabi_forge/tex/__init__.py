"""Reproducible TeX rendering for materials (spec §9.4, §15)."""

from manabi_forge.tex.build import (
    LatexmkNotFoundError,
    TexBuildResult,
    build_material,
    parse_latex_log,
)

__all__ = [
    "LatexmkNotFoundError",
    "TexBuildResult",
    "build_material",
    "parse_latex_log",
]
