"""Gemini 추출기 테스트. 진짜 API 대신 가짜 client를 넣어 응답·에러를 흉내 낸다."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from google.genai import errors

from app.ai import get_extractor
from app.ai.base import ExtractionResult
from app.ai.gemini import ExtractionError, GeminiExtractor, response_schema
from app.config import settings
from app.schemas import ConditionDoc

SAMPLES = Path(__file__).resolve().parents[2] / "samples"

GOOD = json.dumps({
    "full_text": "시급 10,320원",
    "fields": {"wage": {"value": {"type": "시급", "amount_min": 10320, "amount_max": 10320},
                        "quote": "시급 10,320원"}},
}, ensure_ascii=False)


class FakeModels:
    """generate_content가 불릴 때마다 replies에서 하나씩 꺼내 돌려준다 (예외면 던진다)."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = []

    def generate_content(self, *, model, contents, config):
        self.calls.append({"model": model, "contents": contents, "config": config})
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return SimpleNamespace(text=reply)


def make(replies, **kwargs):
    models = FakeModels(replies)
    sleeps = []
    extractor = GeminiExtractor(client=SimpleNamespace(models=models), model="test-model",
                                sleep=sleeps.append, **kwargs)
    return extractor, models, sleeps


def api_error(code):
    return errors.APIError(code, {"error": {"code": code, "message": "x", "status": "X"}})


# --- 4-3 기본 호출 ---

def test_extract_returns_parsed_result():
    extractor, models, _ = make([GOOD])
    result = extractor.extract(b"img", "image/png", "contract")
    assert isinstance(result, ExtractionResult)
    assert result.full_text == "시급 10,320원"
    assert result.fields.wage.value["amount_min"] == 10320


def test_request_uses_model_prompt_and_json_schema():
    extractor, models, _ = make([GOOD])
    extractor.extract(b"img", "image/png", "posting")
    call = models.calls[0]
    assert call["model"] == "test-model"
    part, prompt = call["contents"]
    assert part.inline_data.data == b"img"
    assert part.inline_data.mime_type == "image/png"
    assert '"penalty_or_damages_clause"' in prompt     # extract_v1.md 내용
    assert "채용공고" in prompt                        # doc_kind 안내
    assert call["config"].response_mime_type == "application/json"
    assert call["config"].response_json_schema == response_schema()
    assert call["config"].temperature == 0


# --- Gemini용 응답 스키마 ---

def _walk(node):
    yield node
    if isinstance(node, dict):
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk(v)


def test_response_schema_covers_every_condition_field():
    fields = response_schema()["properties"]["fields"]["properties"]
    assert set(fields) == set(ConditionDoc.model_fields)


def test_every_value_has_a_type():
    """타입 없는 스키마({})나 default 키가 있으면 Gemini가 400을 낸다."""
    fields = response_schema()["properties"]["fields"]["properties"]
    for name, spec in fields.items():
        value = spec["properties"]["value"]
        assert "type" in value or "anyOf" in value, name
    assert not any(isinstance(n, dict) and "default" in n for n in _walk(response_schema()))


def test_wage_value_is_an_object_even_when_undisclosed():
    wage = response_schema()["properties"]["fields"]["properties"]["wage"]["properties"]["value"]
    obj = next(s for s in wage["anyOf"] if s.get("type") == "object")
    assert "비공개" in obj["properties"]["type"]["enum"]


@pytest.mark.parametrize("name", ["case1_posting", "case2_contract", "case3_posting"])
def test_samples_fit_response_schema(name):
    """정답 샘플이 스키마 타입과 맞는지 (number/string/object/null) 간단히 확인."""
    sample = json.loads((SAMPLES / f"{name}.json").read_text(encoding="utf-8"))
    fields = response_schema()["properties"]["fields"]["properties"]
    py = {"string": str, "number": (int, float), "boolean": bool, "object": dict, "null": type(None)}
    for key, item in sample.items():
        allowed = fields[key]["properties"]["value"]["anyOf"]
        assert any(isinstance(item["value"], py[s["type"]]) for s in allowed), key


def test_factory_returns_gemini(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", "test-key")
    monkeypatch.setattr(settings, "gemini_model", "test-model")
    assert isinstance(get_extractor(), GeminiExtractor)


def test_factory_requires_api_key(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", "")
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        get_extractor()


# --- 스키마 검증 + 1회 재시도 ---

def test_invalid_json_is_retried_once():
    extractor, models, _ = make(["not json", GOOD])
    assert extractor.extract(b"img", "image/png", "contract").full_text == "시급 10,320원"
    assert len(models.calls) == 2


def test_schema_violation_is_retried_once():
    bad = json.dumps({"full_text": "x", "fields": {"unknown_field": {}}})
    extractor, models, _ = make([bad, GOOD])
    extractor.extract(b"img", "image/png", "contract")
    assert len(models.calls) == 2


def test_two_invalid_responses_raise_clear_error():
    extractor, models, _ = make(["not json", "still not json"])
    with pytest.raises(ExtractionError, match="스키마"):
        extractor.extract(b"img", "image/png", "contract")
    assert len(models.calls) == 2


def test_empty_response_counts_as_invalid():
    extractor, _, _ = make([None, None])
    with pytest.raises(ExtractionError):
        extractor.extract(b"img", "image/png", "contract")


# --- 429·5xx 지수 백오프 ---

@pytest.mark.parametrize("code", [429, 500, 503])
def test_retryable_errors_back_off_and_succeed(code):
    extractor, models, sleeps = make([api_error(code), api_error(code), GOOD])
    assert extractor.extract(b"img", "image/png", "contract").full_text
    assert sleeps == [10, 20]


def test_gives_up_after_max_retries():
    extractor, models, sleeps = make([api_error(429)] * 4, max_retries=3)
    with pytest.raises(ExtractionError, match="429"):
        extractor.extract(b"img", "image/png", "contract")
    assert len(models.calls) == 4
    assert sleeps == [10, 20, 40]


def test_client_errors_are_not_retried():
    extractor, models, sleeps = make([api_error(400)])
    with pytest.raises(ExtractionError, match="400"):
        extractor.extract(b"img", "image/png", "contract")
    assert len(models.calls) == 1
    assert sleeps == []

