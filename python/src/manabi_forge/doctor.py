"""Environment diagnostics backing the ``manabi doctor`` command.

外部ツールの存在を確認し、制作ワークフローの前提が揃っているかを報告する。
特権的なシステム変更は行わず、修正のヒントを提示するに留める(spec §16.3)。
"""

from __future__ import annotations

import shutil
import sys

from pydantic import BaseModel


class CheckResult(BaseModel):
    """Result of a single environment check."""

    name: str
    required: bool
    ok: bool
    detail: str
    hint: str = ""


class DoctorReport(BaseModel):
    """Aggregated result of all environment checks."""

    checks: list[CheckResult]

    @property
    def ok(self) -> bool:
        """Return ``True`` when every required check passed."""
        return all(check.ok for check in self.checks if check.required)


_TOOLS: tuple[tuple[str, bool, str], ...] = (
    ("git", True, "install Git (https://git-scm.com/)"),
    ("uv", True, "install uv (https://docs.astral.sh/uv/)"),
    ("node", False, "install Node.js >= 20 (https://nodejs.org/)"),
    ("pnpm", False, "run `corepack enable pnpm`"),
    ("latexmk", False, "install TeX Live with the LuaLaTeX toolchain"),
    ("lualatex", False, "install TeX Live with the LuaLaTeX toolchain"),
    ("pdftoppm", False, "install Poppler utilities"),
)

_MIN_PYTHON = (3, 12)


def _check_python() -> CheckResult:
    """Check that the running interpreter satisfies the project minimum."""
    version = sys.version_info
    ok = (version.major, version.minor) >= _MIN_PYTHON
    return CheckResult(
        name="python",
        required=True,
        ok=ok,
        detail=f"{version.major}.{version.minor}.{version.micro}",
        hint="" if ok else "install CPython >= 3.12 (e.g. `uv python install 3.12`)",
    )


def _check_tool(name: str, *, required: bool, hint: str) -> CheckResult:
    """Check that an external command is available on ``PATH``."""
    path = shutil.which(name)
    return CheckResult(
        name=name,
        required=required,
        ok=path is not None,
        detail=path or "not found",
        hint="" if path else hint,
    )


def run_checks() -> DoctorReport:
    """Run every environment check and return the aggregated report."""
    checks = [_check_python()]
    checks.extend(
        _check_tool(name, required=required, hint=hint)
        for name, required, hint in _TOOLS
    )
    return DoctorReport(checks=checks)
