"""Tests for mathematical verification (spec §13.4, §22.4)."""

import json
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from manabi_forge.cli.main import app
from manabi_forge.models import ItemSpec
from manabi_forge.schema_export import find_repo_root
from manabi_forge.verification import verify_item

runner = CliRunner()

MATERIAL_ID = "math1-qf-common-0001"


def make_item(checks: list[dict]) -> ItemSpec:
    return ItemSpec.model_validate(
        {
            "material_id": MATERIAL_ID,
            "stem": "テスト",
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
            "verification_checks": checks,
        },
    )


def quadratic_checks() -> list[dict]:
    return [
        {
            "id": "expansion",
            "kind": "equivalent",
            "expression": "x*(10 - x)",
            "rhs": "-x**2 + 10*x",
        },
        {
            "id": "global-max",
            "kind": "maximum",
            "expression": "-x**2 + 10*x",
            "expected_x": 5,
            "expected_value": 25,
        },
        {
            "id": "restricted-max",
            "kind": "maximum",
            "expression": "-x**2 + 10*x",
            "domain": [2, 4],
            "expected_x": 4,
            "expected_value": 24,
        },
        {
            "id": "restricted-min",
            "kind": "minimum",
            "expression": "-x**2 + 10*x",
            "domain": [2, 4],
            "expected_x": 2,
            "expected_value": 16,
        },
        {
            "id": "vertex",
            "kind": "vertex",
            "expression": "-x**2 + 10*x",
            "expected_x": 5,
            "expected_value": 25,
        },
    ]


class TestVerifyItem:
    def test_correct_quadratic_claims_pass(self):
        report = verify_item(make_item(quadratic_checks()))
        assert report.passed, report.outcomes
        assert not report.failed

    @pytest.mark.parametrize(
        ("field", "wrong"),
        [
            ("expected_value", 26),  # 誤った最大値
            ("expected_x", 3),  # 誤った位置
        ],
    )
    def test_seeded_wrong_answers_are_caught(self, field, wrong):
        # spec §22.4: 仕込んだ数学的欠陥が検出されること
        checks = quadratic_checks()
        checks[1][field] = wrong
        report = verify_item(make_item(checks))
        assert report.failed
        failing = [o for o in report.outcomes if o.status == "failed"]
        assert failing
        assert failing[0].check_id == "global-max"

    def test_wrong_restricted_extremum_is_caught(self):
        checks = quadratic_checks()
        checks[3]["expected_x"] = 4  # 最小は x=2 なのに 4 と主張
        report = verify_item(make_item(checks))
        assert report.failed

    def test_non_equivalent_expression_is_caught(self):
        checks = [
            {
                "id": "expansion",
                "kind": "equivalent",
                "expression": "x*(10 - x)",
                "rhs": "-x**2 + 9*x",
            },
        ]
        assert verify_item(make_item(checks)).failed

    def test_unbounded_maximum_fails(self):
        checks = [
            {
                "id": "impossible",
                "kind": "maximum",
                "expression": "x**2",
                "expected_x": 0,
                "expected_value": 0,
            },
        ]
        report = verify_item(make_item(checks))
        assert report.failed
        assert "unbounded" in report.outcomes[0].detail

    def test_non_unique_maximizer_is_caught(self):
        # x^2 on [-1, 1]: 最大値 1 は x=±1 の 2 点でとる → 一意でない
        checks = [
            {
                "id": "non-unique",
                "kind": "maximum",
                "expression": "x**2",
                "domain": [-1, 1],
                "expected_x": 1,
                "expected_value": 1,
            },
        ]
        report = verify_item(make_item(checks))
        assert report.failed
        assert "unique" in report.outcomes[0].detail

    def test_vertex_requires_quadratic(self):
        checks = [
            {
                "id": "cubic",
                "kind": "vertex",
                "expression": "x**3",
                "expected_x": 0,
                "expected_value": 0,
            },
        ]
        report = verify_item(make_item(checks))
        assert report.outcomes[0].status == "escalated"

    def test_missing_checks_escalate_instead_of_passing(self):
        report = verify_item(make_item([]))
        assert not report.passed
        assert not report.failed
        assert report.outcomes[0].status == "escalated"


class TestSafeGrammar:
    """信頼境界のテスト: 悪意ある式・DoS 式・非有理式が素通りしないこと。"""

    def test_code_injection_is_rejected_at_model_layer(self):
        # SymPy の parse_expr は内部で eval を使うため、英字・下線を含む
        # 文字列がパーサに到達してはならない(spec §19.2)
        with pytest.raises(ValueError, match="safe grammar"):
            make_item(
                [
                    {
                        "id": "evil",
                        "kind": "equivalent",
                        "expression": '__import__("os").system("true")',
                        "rhs": "0",
                    },
                ],
            )

    def test_exponent_tower_is_rejected(self):
        # 9**9**9**9 のような指数タワーは評価前に拒否される(DoS 防止)
        item = make_item(
            [
                {
                    "id": "dos",
                    "kind": "equivalent",
                    "expression": "9**9**9**9",
                    "rhs": "0",
                },
            ],
        )
        report = verify_item(item)
        assert report.outcomes[0].status == "escalated"
        assert "exponent" in report.outcomes[0].detail

    def test_huge_integer_literals_are_rejected_at_model_layer(self):
        with pytest.raises(ValueError, match="10"):
            make_item(
                [
                    {
                        "id": "big",
                        "kind": "equivalent",
                        "expression": "12345678901 * x",
                        "rhs": "0",
                    },
                ],
            )

    def test_transcendental_expressions_are_inexpressible(self):
        # cos(x) は最大値の達成点が無限個あり solve が主枝しか返さないため
        # 誤合格の温床になる。x 以外の英字を許さない文法により、周期関数は
        # そもそもモデル層で表現できない
        with pytest.raises(ValueError, match="safe grammar"):
            make_item(
                [
                    {
                        "id": "periodic",
                        "kind": "maximum",
                        "expression": "cos(x)",
                        "expected_x": 0,
                        "expected_value": 1,
                    },
                ],
            )

    def test_pole_inside_domain_escalates(self):
        # 1/x は [-1, 1] で極を持ち最大・最小が存在しない。
        # passed にせず escalated にする
        item = make_item(
            [
                {
                    "id": "pole",
                    "kind": "minimum",
                    "expression": "1/x",
                    "domain": [-1, 1],
                    "expected_x": -1,
                    "expected_value": -1,
                },
            ],
        )
        report = verify_item(item)
        assert report.outcomes[0].status == "escalated"

    def test_global_extremum_with_real_pole_escalates(self):
        item = make_item(
            [
                {
                    "id": "pole-global",
                    "kind": "maximum",
                    "expression": "1/x",
                    "expected_x": 1,
                    "expected_value": 1,
                },
            ],
        )
        report = verify_item(item)
        assert report.outcomes[0].status == "escalated"

    def test_rational_function_without_real_poles_verifies(self):
        # 1/(1+x^2) は実極を持たず、大域最大 1 を x=0 で一意にとる
        item = make_item(
            [
                {
                    "id": "bell",
                    "kind": "maximum",
                    "expression": "1/(1 + x**2)",
                    "expected_x": 0,
                    "expected_value": 1,
                },
            ],
        )
        report = verify_item(item)
        assert report.passed, report.outcomes

    def test_exact_rational_expected_values_as_strings(self):
        # 期待値は "1/3" のような厳密な有理数文字列で書ける(float の丸め回避)
        item = make_item(
            [
                {
                    "id": "exact",
                    "kind": "minimum",
                    "expression": "3*x**2 - 2*x",
                    "expected_x": "1/3",
                    "expected_value": "-1/3",
                },
            ],
        )
        report = verify_item(item)
        assert report.passed, report.outcomes


class TestRepositoryMaterials:
    def test_committed_common_test_item_verifies(self):
        """コミット済み共通テスト風教材の全主張が SymPy 検証を通ること。"""
        item_path = (
            find_repo_root()
            / "materials"
            / "mathematics"
            / "math-i"
            / "quadratic-functions"
            / MATERIAL_ID
            / "item.yaml"
        )
        item = ItemSpec.model_validate(
            yaml.safe_load(item_path.read_text(encoding="utf-8")),
        )
        report = verify_item(item)
        assert report.passed, report.outcomes


class TestVerifyCli:
    @pytest.fixture
    def material_dir(self, tmp_path) -> Path:
        directory = tmp_path / MATERIAL_ID
        directory.mkdir()
        item = make_item(quadratic_checks())
        (directory / "item.yaml").write_text(
            yaml.safe_dump(item.model_dump(mode="json"), allow_unicode=True),
            encoding="utf-8",
        )
        return directory

    def test_verify_math_passes(self, material_dir):
        result = runner.invoke(app, ["verify", "math", str(material_dir)])
        assert result.exit_code == 0
        assert "verification result: passed" in result.output

    def test_verify_math_json(self, material_dir):
        result = runner.invoke(app, ["verify", "math", "--json", str(material_dir)])
        payload = json.loads(result.output)
        assert all(o["status"] == "passed" for o in payload["outcomes"])

    def test_verify_math_fails_on_seeded_defect(self, material_dir):
        item = make_item(quadratic_checks())
        item.verification_checks[1].expected_value = 30.0
        (material_dir / "item.yaml").write_text(
            yaml.safe_dump(item.model_dump(mode="json"), allow_unicode=True),
            encoding="utf-8",
        )
        result = runner.invoke(app, ["verify", "math", str(material_dir)])
        assert result.exit_code == 1

    def test_missing_item_yaml_is_usage_error(self, tmp_path):
        result = runner.invoke(app, ["verify", "math", str(tmp_path)])
        assert result.exit_code == 2

    def test_record_writes_automated_review(self, material_dir, monkeypatch):
        monkeypatch.setattr(
            "manabi_forge.cli.verify._current_commit",
            lambda _dir: "0123456789abcdef0123456789abcdef01234567",
        )
        result = runner.invoke(
            app,
            ["verify", "math", "--record", str(material_dir)],
        )
        assert result.exit_code == 0
        records = list((material_dir / "reviews").glob("math-auto-*.yaml"))
        assert len(records) == 1
        data = yaml.safe_load(records[0].read_text(encoding="utf-8"))
        assert data["reviewer"]["kind"] == "automated"
        assert data["result"] == "passed"
        # 自動レビューが教材を承認・公開状態にしないこと(ADR-004)は
        # レコードに status 遷移フィールド自体が存在しないことで担保される
        assert "status" not in data
