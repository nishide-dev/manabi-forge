"""Symbolic verification of item claims with SymPy (spec §13.4).

「SymPy passed」は証拠であって、教育的解答の正しさや適切さの証明ではない
(spec §13.4)。対応できない主張は明示的に escalated として返し、
黙って合格扱いにしない。

安全性(spec §19.2): 式はモデル層(SAFE_EXPRESSION_PATTERN)とここでの
二重の文法検証を通ったもののみを SymPy に渡す。許可文法は x・数字・四則・
べき・括弧のみで、英字名や下線を含む文字列は SymPy のパーサ(内部で eval を
使う)に到達しない。べき指数は整数リテラル ±12 以内に制限し、パース・求解の
計算量を抑える。数学的な健全性のため、検証対象は実特異点の解析ができる
多項式・有理式に限定し、それ以外(周期関数等)は escalated にする。
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

import sympy
from pydantic import BaseModel, ConfigDict, Field
from sympy.parsing.sympy_parser import parse_expr, standard_transformations

from manabi_forge.models.item import (
    VerificationCheck,
    VerificationKind,
    validate_safe_expression,
)

if TYPE_CHECKING:
    from manabi_forge.models import ItemSpec

X = sympy.Symbol("x", real=True)

_MAX_POW_EXPONENT = 12

#: parse_expr の変換済みコードが参照する安全なコンストラクタのみを提供する。
#: 文法ゲートで英字・下線は既に拒否されているため、ここに任意名は現れない。
_SAFE_GLOBALS: dict[str, object] = {
    "Symbol": sympy.Symbol,
    "Integer": sympy.Integer,
    "Float": sympy.Float,
    "Rational": sympy.Rational,
    "Add": sympy.Add,
    "Mul": sympy.Mul,
    "Pow": sympy.Pow,
}


class UnsupportedExpressionError(ValueError):
    """Raised when an expression falls outside the supported safe subset."""


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


def _safe_parse(expression: str, *, allow_x: bool = True) -> sympy.Expr:
    """Parse an expression after enforcing the safe grammar.

    パース後も式木を走査し、未知シンボル・関数適用・整数リテラル以外の
    べき指数を拒否する(``9**9**9`` のような指数タワーの DoS を防ぐ)。
    """
    validate_safe_expression(expression, allow_x=allow_x)
    try:
        expr = parse_expr(
            expression,
            local_dict={"x": X},
            global_dict=dict(_SAFE_GLOBALS),
            transformations=standard_transformations,
            evaluate=False,
        )
    except (SyntaxError, TypeError, ValueError, sympy.SympifyError) as exc:
        msg = f"cannot parse expression {expression!r}: {exc}"
        raise UnsupportedExpressionError(msg) from exc
    if not isinstance(expr, sympy.Expr):
        msg = f"expression {expression!r} is not a mathematical expression"
        raise UnsupportedExpressionError(msg)
    allowed_symbols = {X} if allow_x else set()
    if not expr.free_symbols <= allowed_symbols:
        extra = expr.free_symbols - allowed_symbols
        msg = f"expression {expression!r} uses unsupported symbols: {extra}"
        raise UnsupportedExpressionError(msg)
    for node in sympy.preorder_traversal(expr):
        if isinstance(node, sympy.Pow):
            exponent = node.exp
            if not (exponent.is_Integer and abs(int(exponent)) <= _MAX_POW_EXPONENT):
                msg = (
                    f"expression {expression!r} has an unsupported exponent "
                    f"(integer literals within ±{_MAX_POW_EXPONENT} only)"
                )
                raise UnsupportedExpressionError(msg)
    return expr


def _rational(value: float) -> sympy.Rational:
    """Convert a YAML number to an exact rational for symbolic comparison."""
    return sympy.Rational(str(value))


def _expected_constant(value: float | str | None) -> sympy.Expr:
    """Convert an expected value (number or safe constant string like "1/3")."""
    if value is None:
        msg = "expected value is missing"
        raise UnsupportedExpressionError(msg)
    if isinstance(value, str):
        return sympy.nsimplify(_safe_parse(value, allow_x=False))
    return _rational(value)


def _real_singularities(expr: sympy.Expr) -> list[sympy.Expr]:
    """Return the real singularities of a rational function."""
    return [point for point in sympy.singularities(expr, X) if point.is_real]


def _extrema_candidates(
    expr: sympy.Expr,
    domain: tuple[float, float] | None,
) -> list[sympy.Expr] | None:
    """Return candidate extremum points, or ``None`` when unsupported.

    有理式に限定しているため solve(diff) は候補を網羅する(周期関数の
    主枝切り捨てのような取りこぼしは起きない)。
    """
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


def _escalate(check_id: str, detail: str) -> CheckOutcome:
    return CheckOutcome(
        check_id=check_id,
        status=OutcomeStatus.ESCALATED,
        detail=detail,
    )


def _extremum_precheck(
    check: VerificationCheck,
    expr: sympy.Expr,
) -> CheckOutcome | None:
    """Gate the extremum analysis: 有理式限定・特異点・非有界性の検査."""
    if not expr.is_rational_function(X):
        return _escalate(
            check.id,
            "only polynomial or rational expressions are machine-checkable; "
            "manual review required",
        )
    singular = _real_singularities(expr)
    if check.domain is None:
        if singular:
            return _escalate(
                check.id,
                f"expression has real singularities at {singular}; "
                "global extremum requires manual review",
            )
        if not _is_globally_bounded(expr, check.kind):
            return CheckOutcome(
                check_id=check.id,
                status=OutcomeStatus.FAILED,
                detail=f"{check.kind.value} does not exist: expression is unbounded",
            )
    else:
        low, high = _rational(check.domain[0]), _rational(check.domain[1])
        inside = [s for s in singular if bool(low <= s) and bool(s <= high)]
        if inside:
            return _escalate(
                check.id,
                f"domain contains singularities at {inside}; "
                "extremum claim requires manual review",
            )
    return None


def _check_extremum(check: VerificationCheck) -> CheckOutcome:
    expr = _safe_parse(check.expression)
    gate = _extremum_precheck(check, expr)
    if gate is not None:
        return gate

    candidates = _extrema_candidates(expr, check.domain)
    if candidates is None or not candidates:
        return _escalate(
            check.id,
            "no usable extremum candidates; manual review required",
        )

    values = [(point, sympy.simplify(expr.subs(X, point))) for point in candidates]
    pick = max if check.kind is VerificationKind.MAXIMUM else min
    best_value = pick(value for _point, value in values)
    best_points = {
        sympy.nsimplify(point)
        for point, value in values
        if sympy.simplify(value - best_value) == 0
    }

    expected_x = _expected_constant(check.expected_x)
    expected_value = _expected_constant(check.expected_value)
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
    expr = _safe_parse(check.expression)
    poly = expr.as_poly(X)
    quadratic_degree = 2
    if poly is None or poly.degree() != quadratic_degree:
        return _escalate(
            check.id,
            "vertex check requires a quadratic polynomial in x",
        )
    a, b = poly.all_coeffs()[0], poly.all_coeffs()[1]
    vertex_x = sympy.Rational(-b, 2 * a)
    vertex_y = sympy.simplify(expr.subs(X, vertex_x))
    if sympy.simplify(vertex_x - _expected_constant(check.expected_x)) != 0 or (
        sympy.simplify(vertex_y - _expected_constant(check.expected_value)) != 0
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
    lhs = _safe_parse(check.expression)
    rhs = _safe_parse(check.rhs or "")
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
    except (
        UnsupportedExpressionError,
        ValueError,
        TypeError,
        SyntaxError,
        sympy.SympifyError,
    ) as exc:
        return _escalate(check.id, f"could not evaluate check: {exc}")


def verify_item(item: ItemSpec) -> VerificationReport:
    """Run every machine check of one item.

    verification_checks が空の場合は escalated 1 件のレポートを返す。
    自動検証の対象がないことは「合格」ではない(spec §13.4)。
    """
    if not item.verification_checks:
        return VerificationReport(
            material_id=item.material_id,
            outcomes=[
                _escalate(
                    "coverage",
                    "item has no machine-checkable verification_checks; "
                    "manual mathematical review required",
                ),
            ],
        )
    return VerificationReport(
        material_id=item.material_id,
        outcomes=[_run_check(check) for check in item.verification_checks],
    )
