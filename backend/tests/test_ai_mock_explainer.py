import pytest

from app.ai import get_explainer
from app.ai.mock import QUESTION_TEMPLATES, TEMPLATE_VERSION, MockExplainer
from app.config import settings
from app.schemas import Finding


def finding(level, item="수습", message="공고 수습 없음 → 계약서 수습 3개월"):
    return Finding(level=level, item=item, message=message)


def test_explains_every_finding_except_same_or_better():
    findings = [finding("불리 변경"), finding("동일·유리", item="전체"), finding("누락", item="연차유급휴가")]
    result = MockExplainer().explain(findings)
    assert result.prompt_version == TEMPLATE_VERSION
    assert [i.item for i in result.items] == ["수습", "연차유급휴가"]


def test_summary_is_engine_message_and_question_names_item():
    item = MockExplainer().explain([finding("불리 변경")]).items[0]
    assert item.summary == "공고 수습 없음 → 계약서 수습 3개월"
    assert "'수습'" in item.question and item.question.endswith("?")


@pytest.mark.parametrize("level", list(QUESTION_TEMPLATES))
def test_every_level_has_polite_question(level):
    question = MockExplainer().explain([finding(level)]).items[0].question
    assert "주실 수 있을까요?" in question


def test_no_findings_gives_no_items():
    assert MockExplainer().explain([]).items == []


def test_factory_returns_mock_explainer(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "mock")
    assert isinstance(get_explainer(), MockExplainer)


def test_factory_rejects_unknown_provider(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "nope")
    with pytest.raises(ValueError, match="nope"):
        get_explainer()
