"""Curriculum knowledge base access (spec §10)."""

from manabi_forge.curriculum.store import (
    CurriculumStore,
    DuplicateCodeError,
    load_store,
)

__all__ = [
    "CurriculumStore",
    "DuplicateCodeError",
    "load_store",
]
