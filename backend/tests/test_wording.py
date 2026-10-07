import json
from pathlib import Path

import pytest

from app.ai.mock import MockExplainer
from app.ai.wording import assertive_words, is_safe
from app.rules.engine import compare
from app.schemas import ConditionDoc, ExplanationItem

SAMPLES = Path(__file__).resolve().parents[2] / "samples"


def item(summary="", question=""):
    return ExplanationItem(item="수습", summary=summary, question=question)


@pytest.mark.parametrize("text", ["근로기준법 위반입니다", "불법 계약이에요", "위법 소지가 있습니다", "처벌받을 수 있어요"])
def test_assertive_wording_is_unsafe(text):
    assert assertive_words(text)
    assert not is_safe(item(summary=text))
    assert not is_safe(item(question=text))


def test_polite_check_wording_is_safe():
    assert is_safe(item("공고와 계약서의 수습 조건이 달라 확인이 필요합니다.",
                        "수습 기간이 어떻게 정해졌는지 확인해 주실 수 있을까요?"))


@pytest.mark.parametrize("case", sorted(json.loads((SAMPLES / "answer_key.json").read_text(encoding="utf-8"))))
def test_template_explanations_for_samples_are_safe(case):
    """고정 문구(엔진 메시지 + 질문 틀)는 단정 표현이 없어야 대체 문구로 쓸 수 있다."""
    def load(kind):
        return ConditionDoc.model_validate_json((SAMPLES / f"{case}_{kind}.json").read_text(encoding="utf-8"))
    explanation = MockExplainer().explain(compare(load("posting"), load("contract")))
    assert all(is_safe(i) for i in explanation.items)
