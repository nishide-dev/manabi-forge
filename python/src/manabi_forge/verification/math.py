"""Symbolic verification of item claims with SymPy (spec §13.4).

「SymPy passed」は証拠であって、教育的解答の正しさや適切さの証明ではない
(spec §13.4)。対応できない主張は明示的に escalated として返し、
黙って合格扱いにしない。
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

import sympy
from pydantic import BaseModel, ConfigDict, Field
from sympy.parsing.sympy_parser import parse_expr

from manabi_forge.models.item import VerificationCheck, VerificationKind

if TYPE_CHECKING:
    from manabi_forge.models import ItemSpec

X = sympy.Symbol("x", real=True)


class OutcomeStatus(StrEnum):
    """Result of one machine check."""

    PASSED = "passed"
    FAILED = "failed"
    ESCALATED = "escalated"


class CheckOutcome(BaseModel):
    """Outcome of one verification check."""

    model_config = ConfigDict(extra="forbid")

    check_id: str
    status: OutcomeStatus
    detail: str


class VerificationReport(BaseModel):
    """Aggregated verification result for one item."""

    model_config = ConfigDict(extra="forbid")

    material_id: str
    outcomes: list[CheckOutcome] = Field(default_factory=list)

    @property
    def passed(self) -> bool:
        """True when every check passed (escalations are not passes)."""
        return bool(self.outcomes) and all(
            outcome.status is OutcomeStatus.PASSED for outcome in self.outcomes
        )

    @property
    def failed(self) -> bool:
        """True when any check demonstrably failed."""
        return any(outcome.status is OutcomeStatus.FAILED for outcome in self.outcomes)


def _parse(expression: str) -> sympy.Expr:
    """Parse a SymPy expression in x. eval を使う sympify ではなく parse_expr を使う."""
    return parse_expr(expression, local_dict={"x": X}, evaluate=True)


def _rational(value: float) -> sympy.Rational:
    """Convert a YAML number to an exact rational for symbolic comparison."""
    return sympy.Rational(str(value))


def _extrema_candidates(
    expr: sympy.Expr,
    domain: tuple[float, float] | None,
) -> list[sympy.Expr] | None:
    """Return candidate extremum points, or ``None`` when unsupported."""
    try:
        critical = sympy.solve(sympy.diff(expr, X), X)
    except (NotImplementedError, ValueError):
        return None
    candidates = [point for point in critical if point.is_real]
    if domain is not None:
        low, high = _rational(domain[0]), _rational(domain[1])
        candidates = [p for p in candidates if bool(low <= p) and bool(p <= high)]
        candidates.extend([low, high])
    return candidates


def _is_globally_bounded(expr: sympy.Expr, kind: VerificationKind) -> bool:
    """Check that a global extremum exists (limits at ±∞ do not diverge that way)."""
    direction = sympy.oo if kind is VerificationKind.MAXIMUM else -sympy.oo
    for point in (sympy.oo, -sympy.oo):
        limit = sympy.limit(expr, X, point)
        if limit == direction:
            return False
    return True


def _check_extremum(check: VerificationCheck) -> CheckOutcome:
    expr = _parse(check.expression)
    if check.domain is None and not _is_globally_bounded(expr, check.kind):
        return CheckOutcome(
            check_id=check.id,
            status=OutcomeStatus.FAILED,
            detail=f"{check.kind.value} does not exist: expression is unbounded",
        )
    candidates = _extrema_candidates(expr, check.domain)
    if candidates is None or not candidates:
        return CheckOutcome(
            check_id=check.id,
            status=OutcomeStatus.ESCALATED,
            detail="no usable extremum candidates; manual review required",
        )

    values = [(point, sympy.simplify(expr.subs(X, point))) for point in candidates]
    pick = max if check.kind is VerificationKind.MAXIMUM else min
    best_value = pick(value for _point, value in values)
    best_points = {
        sympy.nsimplify(point)
        for point, value in values
        if sympy.simplify(value - best_value) == 0
    }

    expected_x = _rational(check.expected_x or 0)
    expected_value = _rational(check.expected_value or 0)
    if sympy.simplify(best_value - expected_value) != 0:
        return CheckOutcome(
            check_id=check.id,
            status=OutcomeStatus.FAILED,
            detail=f"expected {check.kind.value} {expected_value}, got {best_value}",
        )
    if best_points != {expected_x}:
        return CheckOutcome(
            check_id=check.id,
            status=OutcomeStatus.FAILED,
            detail=(
                f"expected unique argument x={expected_x}, "
                f"got {sorted(best_points, key=str)}"
            ),
        )
    return CheckOutcome(
        check_id=check.id,
        status=OutcomeStatus.PASSED,
        detail=f"{check.kind.value} {best_value} at x={expected_x} confirmed",
    )


def _check_vertex(check: VerificationCheck) -> CheckOutcome:
    expr = _parse(check.expression)
    poly = expr.as_poly(X)
    quadratic_degree = 2
    if poly is None or poly.degree() != quadratic_degree:
        return CheckOutcome(
            check_id=check.id,
            status=OutcomeStatus.ESCALATED,
            detail="vertex check requires a quadratic polynomial in x",
        )
    a, b = poly.all_coeffs()[0], poly.all_coeffs()[1]
    vertex_x = sympy.Rational(-b, 2 * a)
    vertex_y = sympy.simplify(expr.subs(X, vertex_x))
    if sympy.simplify(vertex_x - _rational(check.expected_x or 0)) != 0 or (
        sympy.simplify(vertex_y - _rational(check.expected_value or 0)) != 0
    ):
        return CheckOutcome(
            check_id=check.id,
            status=OutcomeStatus.FAILED,
            detail=f"vertex is ({vertex_x}, {vertex_y})",
        )
    return CheckOutcome(
        check_id=check.id,
        status=OutcomeStatus.PASSED,
        detail=f"vertex ({vertex_x}, {vertex_y}) confirmed",
    )


def _check_equivalent(check: VerificationCheck) -> CheckOutcome:
    lhs = _parse(check.expression)
    rhs = _parse(check.rhs or "")
    if sympy.simplify(lhs - rhs) != 0:
        return CheckOutcome(
            check_id=check.id,
            status=OutcomeStatus.FAILED,
            detail=f"{check.expression} is not equivalent to {check.rhs}",
        )
    return CheckOutcome(
        check_id=check.id,
        status=OutcomeStatus.PASSED,
        detail="expressions are equivalent",
    )


def _run_check(check: VerificationCheck) -> CheckOutcome:
    try:
        if check.kind in {VerificationKind.MAXIMUM, VerificationKind.MINIMUM}:
            return _check_extremum(check)
        if check.kind is VerificationKind.VERTEX:
            return _check_vertex(check)
        return _check_equivalent(check)
    except (ValueError, TypeError, SyntaxError, sympy.SympifyError) as exc:
        return CheckOutcome(
            check_id=check.id,
            status=OutcomeStatus.ESCALATED,
            detail=f"could not evaluate check: {exc}",
        )


def verify_item(item: ItemSpec) -> VerificationReport:
    """Run every machine check of one item.

    verification_checks が空の場合は escalated 1 件のレポートを返す。
    自動検証の対象がないことは「合格」ではない(spec §13.4)。
    """
    if not item.verification_checks:
        return VerificationReport(
            material_id=item.material_id,
            outcomes=[
                CheckOutcome(
                    check_id="coverage",
                    status=OutcomeStatus.ESCALATED,
                    detail=(
                        "item has no machine-checkable verification_checks; "
                        "manual mathematical review required"
                    ),
                ),
            ],
        )
    return VerificationReport(
        material_id=item.material_id,
        outcomes=[_run_check(check) for check in item.verification_checks],
    )
