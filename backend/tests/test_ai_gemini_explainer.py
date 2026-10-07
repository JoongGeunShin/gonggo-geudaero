"""Gemini 설명기 테스트. 진짜 API 대신 가짜 client를 넣는다 (test_ai_gemini.py와 같은 방식)."""

import json
from types import SimpleNamespace

import pytest

from app.ai import get_explainer
from app.ai.base import ExplanationError
from app.ai.gemini import GeminiExplainer, explain_schema
from app.ai.prompts import EXPLAIN_PROMPT_VERSION
from app.config import settings
from app.schemas import Finding
from tests.test_ai_gemini import FakeModels, api_error

FINDINGS = [
    Finding(level="불리 변경", item="수습", message="공고 수습 없음 → 계약서 수습 3개월"),
    Finding(level="누락", item="연차유급휴가", message="계약서에 기재 없음", basis="근로기준법 제60조"),
    Finding(level="동일·유리", item="근무지", message="같음"),
]


def reply(*items):
    return json.dumps({"items": [{"item": i, "summary": f"{i} 설명", "question": f"{i} 확인해 주실 수 있을까요?"}
                                 for i in items]}, ensure_ascii=False)


def make(replies):
    models = FakeModels(replies)
    sleeps = []
    explainer = GeminiExplainer(client=SimpleNamespace(models=models), model="lite-model", sleep=sleeps.append)
    return explainer, models, sleeps


def test_explain_returns_items_in_finding_order():
    explainer, _, _ = make([reply("연차유급휴가", "수습")])   # 모델이 순서를 바꿔도
    result = explainer.explain(FINDINGS)
    assert result.prompt_version == EXPLAIN_PROMPT_VERSION
    assert [i.item for i in result.items] == ["수습", "연차유급휴가"]
    assert result.items[0].summary == "수습 설명"


def test_request_sends_only_non_favorable_findings_as_text():
    explainer, models, _ = make([reply("수습", "연차유급휴가")])
    explainer.explain(FINDINGS)
    call = models.calls[0]
    assert call["model"] == "lite-model"
    [prompt] = call["contents"]                     # 이미지 없이 글자 하나
    assert "확인이 필요합니다" in prompt              # explain_v1.md 내용
    assert "계약서 수습 3개월" in prompt and "근로기준법 제60조" in prompt
    assert "근무지" not in prompt.split("## 판정 결과")[1]   # 동일·유리는 보내지 않음
    assert call["config"].response_json_schema == explain_schema()


def test_missing_or_renamed_items_fall_back_to_template():
    explainer, _, _ = make([reply("수습기간")])      # '수습'을 바꿔 쓰고, 연차는 빠뜨림
    items = explainer.explain(FINDINGS).items
    assert [i.item for i in items] == ["수습", "연차유급휴가"]
    assert items[0].summary == "공고 수습 없음 → 계약서 수습 3개월"   # 고정 문구 = 엔진 메시지


def test_no_targets_skips_the_call():
    explainer, models, _ = make([])
    assert explainer.explain([FINDINGS[2]]).items == []
    assert models.calls == []


def test_invalid_json_is_retried_once_then_raises():
    explainer, models, _ = make(["not json", "still not json"])
    with pytest.raises(ExplanationError, match="스키마"):
        explainer.explain(FINDINGS)
    assert len(models.calls) == 2


def test_api_error_retries_once_then_raises_explanation_error():
    explainer, models, sleeps = make([api_error(503), api_error(503)])
    with pytest.raises(ExplanationError, match="503"):
        explainer.explain(FINDINGS)
    assert sleeps == [10]   # 설명은 대체 문구가 있으니 재시도 1번만


def test_factory_uses_explain_model_or_falls_back(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(settings, "gemini_model", "big-model")
    monkeypatch.setattr(settings, "gemini_explain_model", "")
    assert get_explainer().model == "big-model"
    monkeypatch.setattr(settings, "gemini_explain_model", "lite-model")
    assert get_explainer().model == "lite-model"


def test_factory_requires_api_key(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", "")
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        get_explainer()
