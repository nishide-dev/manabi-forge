"""Tests for the Pydantic data models (spec §11)."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from manabi_forge.models import (
    ItemSpec,
    MaterialManifest,
    ProvenanceRecord,
    ReleaseManifest,
    ReviewRecord,
)


def make_material_data() -> dict:
    """Return a valid material.yaml payload based on the spec §11.3 example."""
    return {
        "schema_version": "1.0",
        "id": "math1-qf-common-0001",
        "version": "0.1.0",
        "title": "二次関数と最大・最小",
        "language": "ja",
        "status": "draft",
        "classification": {
            "school_level": "high-school",
            "subject": "mathematics",
            "course": "mathematics-i",
            "units": ["quadratic-functions"],
            "format": "common-test-style",
            "difficulty": "standard",
            "estimated_minutes": 15,
            "audience": ["learner"],
        },
        "curriculum": {
            "snapshot": "mext-84V10-2026-08",
            "codes": ["84V10-quadratic-functions"],
            "alignment_status": "pending",
        },
        "provenance": {
            "ai_assisted": True,
            "origin": "original",
            "source_text_included": False,
        },
    }


class TestMaterialManifest:
    def test_accepts_spec_example(self):
        manifest = MaterialManifest.model_validate(make_material_data())
        assert manifest.id == "math1-qf-common-0001"
        assert manifest.validation.schema_check.value == "pending"
        assert manifest.license.content == "CC-BY-4.0"

    @pytest.mark.parametrize(
        "bad_id",
        [
            "Math1-qf-common-0001",  # 大文字
            "math1_qf_common_0001",  # アンダースコア
            "math1-qf-common-1",  # 連番が 4 桁でない
            "math1-qf-common-0001-",  # 末尾ハイフン
            "0001",  # 連番のみ
        ],
    )
    def test_rejects_malformed_id(self, bad_id):
        data = make_material_data()
        data["id"] = bad_id
        with pytest.raises(ValidationError):
            MaterialManifest.model_validate(data)

    def test_rejects_unknown_fields(self):
        data = make_material_data()
        data["unknown_field"] = "x"
        with pytest.raises(ValidationError):
            MaterialManifest.model_validate(data)

    def test_validation_block_accepts_schema_alias(self):
        data = make_material_data()
        data["validation"] = {"schema": "passed"}
        manifest = MaterialManifest.model_validate(data)
        assert manifest.validation.schema_check.value == "passed"
        dumped = manifest.model_dump(by_alias=True)
        assert dumped["validation"]["schema"] == "passed"

    def test_default_dump_round_trips(self):
        # model_dump() の既定出力をそのまま再読込できること(alias 起因の
        # write-only フィールドが存在しないことの回帰テスト)。
        manifest = MaterialManifest.model_validate(make_material_data())
        reloaded = MaterialManifest.model_validate(manifest.model_dump(mode="json"))
        assert reloaded == manifest

    @pytest.mark.parametrize(
        "good_id",
        [
            "math1-quadratic-functions-common-test-style-0001",  # 複数語セグメント
            "math1-qf-guided-0001",
            "info1-network-basics-worksheet-0203",
        ],
    )
    def test_accepts_multi_word_id_segments(self, good_id):
        data = make_material_data()
        data["id"] = good_id
        assert MaterialManifest.model_validate(data).id == good_id


def make_item_data() -> dict:
    """Return a valid item.yaml payload."""
    return {
        "material_id": "math1-qf-common-0001",
        "stem": "二次関数 y = x^2 - 4x + 5 について考える。",
        "parts": [
            {
                "id": "a",
                "prompt": "頂点の座標を求めよ。",
                "answer_type": "multiple-choice",
                "correct_answer": "2",
                "choices": [
                    {"label": "1", "text": "(2, -1)", "rationale": "符号の取り違え"},
                    {"label": "2", "text": "(2, 1)", "is_correct": True},
                    {
                        "label": "3",
                        "text": "(-2, 1)",
                        "rationale": "平方完成の符号ミス",
                    },
                ],
            },
        ],
        "required_knowledge": ["平方完成"],
        "intended_reasoning": "平方完成により頂点を特定する。",
        "solution_outline": "y = (x-2)^2 + 1 と変形し頂点 (2, 1) を得る。",
        "verification_strategy": "SymPy で頂点を計算し選択肢の一意性を確認する。",
    }


class TestItemSpec:
    def test_accepts_valid_item(self):
        item = ItemSpec.model_validate(make_item_data())
        assert item.parts[0].answer_type.value == "multiple-choice"

    def test_rejects_two_correct_choices(self):
        data = make_item_data()
        data["parts"][0]["choices"][0]["is_correct"] = True
        with pytest.raises(ValidationError, match="exactly 1 correct choice"):
            ItemSpec.model_validate(data)

    def test_rejects_choices_on_non_choice_part(self):
        data = make_item_data()
        data["parts"][0]["answer_type"] = "numeric"
        with pytest.raises(ValidationError, match="only allowed for multiple-choice"):
            ItemSpec.model_validate(data)

    def test_rejects_duplicate_part_ids(self):
        data = make_item_data()
        part = dict(data["parts"][0])
        part["choices"] = list(data["parts"][0]["choices"])
        data["parts"] = [data["parts"][0], part]
        with pytest.raises(ValidationError, match="duplicate part ids"):
            ItemSpec.model_validate(data)

    def test_rejects_duplicate_choice_labels(self):
        data = make_item_data()
        data["parts"][0]["choices"][0]["label"] = "2"
        data["parts"][0]["choices"][1]["is_correct"] = True
        with pytest.raises(ValidationError, match="labels must be unique"):
            ItemSpec.model_validate(data)

    def test_rejects_correct_answer_not_matching_correct_choice(self):
        data = make_item_data()
        data["parts"][0]["correct_answer"] = "99"
        with pytest.raises(ValidationError, match="does not match the correct choice"):
            ItemSpec.model_validate(data)

    def test_round_trips_default_dump(self):
        item = ItemSpec.model_validate(make_item_data())
        assert ItemSpec.model_validate(item.model_dump(mode="json")) == item


def make_review_data() -> dict:
    """Return a valid review record payload based on the spec §11.5 example."""
    return {
        "material_id": "math1-qf-common-0001",
        "review_id": "math-review-2026-0001",
        "review_type": "mathematics",
        "reviewer": {"kind": "human", "name": "contributor-id"},
        "reviewed_commit": "0123456789abcdef0123456789abcdef01234567",
        "result": "changes-requested",
        "findings": [
            {
                "severity": "high",
                "location": "item.parts[0]",
                "code": "non-unique-answer",
                "message": "条件のもとで選択肢が複数成立する。",
                "suggested_action": "条件を追加する。",
            },
        ],
        "created_at": datetime(2026, 8, 16, tzinfo=UTC),
    }


class TestReviewRecord:
    def test_accepts_spec_example(self):
        record = ReviewRecord.model_validate(make_review_data())
        assert record.findings[0].severity.value == "high"

    def test_automated_reviewer_requires_tool_version(self):
        data = make_review_data()
        data["reviewer"] = {"kind": "automated", "name": "manabi-verify"}
        with pytest.raises(ValidationError, match="tool_version"):
            ReviewRecord.model_validate(data)

    def test_changes_requested_requires_findings(self):
        data = make_review_data()
        data["findings"] = []
        with pytest.raises(ValidationError, match="at least one finding"):
            ReviewRecord.model_validate(data)


class TestProvenanceRecord:
    def test_requires_human_author(self):
        with pytest.raises(ValidationError):
            ProvenanceRecord.model_validate(
                {"material_id": "math1-qf-common-0001", "authors": []},
            )

    def test_accepts_ai_steps_without_raw_prompts(self):
        record = ProvenanceRecord.model_validate(
            {
                "material_id": "math1-qf-common-0001",
                "authors": ["nishide-dev"],
                "ai_steps": [
                    {
                        "description": "draft item from brief",
                        "model": "claude-fable-5",
                        "prompt_hash": "a" * 64,
                    },
                ],
            },
        )
        assert record.ai_steps[0].model == "claude-fable-5"

    def test_rejects_non_sha256_prompt_hash(self):
        with pytest.raises(ValidationError):
            ProvenanceRecord.model_validate(
                {
                    "material_id": "math1-qf-common-0001",
                    "authors": ["nishide-dev"],
                    "ai_steps": [
                        {"description": "draft", "prompt_hash": "not-a-hash"},
                    ],
                },
            )

    def test_rejects_prompt_summary_long_enough_to_be_a_raw_prompt(self):
        # 500 文字超の「要約」はプロンプト原文の混入とみなして拒否(spec §11.6)
        with pytest.raises(ValidationError):
            ProvenanceRecord.model_validate(
                {
                    "material_id": "math1-qf-common-0001",
                    "authors": ["nishide-dev"],
                    "ai_steps": [
                        {"description": "draft", "prompt_summary": "x" * 501},
                    ],
                },
            )


ALL_REVIEWS_PASSED = {
    "mathematics": "passed",
    "curriculum": "passed",
    "editorial": "passed",
    "visual": "passed",
    "rights": "passed",
}


def make_release_data() -> dict:
    """Return a valid Appendix B style release manifest payload."""
    return {
        "materialId": "math1-qf-common-0001",
        "materialVersion": "1.0.0",
        "sourceCommit": "0123456789abcdef",
        "curriculumSnapshot": "mext-84V10-2026-08",
        "template": {"id": "common-test", "version": "1.0.0"},
        "reviews": dict(ALL_REVIEWS_PASSED),
        "artifacts": [
            {
                "kind": "problem-pdf",
                "filename": "math1-qf-common-0001-v1.0.0-problem.pdf",
                "sha256": "a" * 64,
            },
        ],
    }


class TestReleaseManifest:
    def test_serializes_camel_case_like_appendix_b(self):
        manifest = ReleaseManifest.model_validate(make_release_data())
        dumped = manifest.model_dump(by_alias=True)
        assert dumped["materialId"] == "math1-qf-common-0001"
        assert dumped["curriculumSnapshot"] == "mext-84V10-2026-08"

    def test_accepts_snake_case_input_too(self):
        data = make_release_data()
        data["material_id"] = data.pop("materialId")
        data["material_version"] = data.pop("materialVersion")
        data["source_commit"] = data.pop("sourceCommit")
        data["curriculum_snapshot"] = data.pop("curriculumSnapshot")
        manifest = ReleaseManifest.model_validate(data)
        assert manifest.material_version == "1.0.0"

    def test_rejects_missing_required_review(self):
        # 必須レビューの欠落は人間公開ゲート(ADR-004)の迂回になるため拒否
        data = make_release_data()
        del data["reviews"]["rights"]
        with pytest.raises(ValidationError, match="missing required reviews"):
            ReleaseManifest.model_validate(data)

    def test_rejects_empty_reviews(self):
        data = make_release_data()
        data["reviews"] = {}
        with pytest.raises(ValidationError, match="missing required reviews"):
            ReleaseManifest.model_validate(data)

    def test_rejects_non_passed_review(self):
        data = make_release_data()
        data["reviews"]["mathematics"] = "failed"
        with pytest.raises(ValidationError, match="non-passed reviews"):
            ReleaseManifest.model_validate(data)

    def test_rejects_unknown_review_type(self):
        data = make_release_data()
        data["reviews"]["totally-made-up"] = "passed"
        with pytest.raises(ValidationError):
            ReleaseManifest.model_validate(data)
