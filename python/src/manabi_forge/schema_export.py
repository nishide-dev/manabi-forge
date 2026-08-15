"""JSON Schema export for the Pydantic models (spec §9.3).

Pydantic モデルが正であり、生成された JSON Schema Draft 2020-12 を `schemas/` に
コミットする。出力は決定論的で、再生成により追跡ファイルが変化した場合は
CI が失敗する。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from manabi_forge.models import (
    ItemSpec,
    MaterialManifest,
    ProvenanceRecord,
    ReleaseManifest,
    ReviewRecord,
)

if TYPE_CHECKING:
    from pydantic import BaseModel

JSON_SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"

SCHEMA_EXPORTS: dict[str, type[BaseModel]] = {
    "material.schema.json": MaterialManifest,
    "item.schema.json": ItemSpec,
    "review.schema.json": ReviewRecord,
    "provenance.schema.json": ProvenanceRecord,
    "release.schema.json": ReleaseManifest,
}


class RepoRootNotFoundError(RuntimeError):
    """Raised when the repository root cannot be located from the start path."""


def find_repo_root(start: Path | None = None) -> Path:
    """Walk upwards from ``start`` (default: cwd) to the directory containing .git."""
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    msg = f"no .git directory found above {current}"
    raise RepoRootNotFoundError(msg)


def render_schema(model: type[BaseModel]) -> str:
    """Render one model's JSON Schema as deterministic, committed-file text."""
    schema = model.model_json_schema()
    schema["$schema"] = JSON_SCHEMA_DIALECT
    return json.dumps(schema, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def write_schemas(out_dir: Path) -> list[Path]:
    """Write every exported schema into ``out_dir`` and return the written paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for filename, model in SCHEMA_EXPORTS.items():
        path = out_dir / filename
        path.write_text(render_schema(model), encoding="utf-8")
        written.append(path)
    return written


def check_schemas(out_dir: Path) -> list[str]:
    """Return the schema filenames that are missing or stale in ``out_dir``."""
    stale: list[str] = []
    for filename, model in SCHEMA_EXPORTS.items():
        path = out_dir / filename
        if not path.is_file() or path.read_text(encoding="utf-8") != render_schema(
            model
        ):
            stale.append(filename)
    return stale
