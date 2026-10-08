import json
from pathlib import Path

import pytest

from app.ai import get_extractor
from app.ai.mock import MockExtractor
from app.config import settings
from app.schemas import ConditionDoc

SAMPLES = Path(__file__).resolve().parents[2] / "samples"


def _sample(name: str) -> ConditionDoc:
    return ConditionDoc.model_validate_json((SAMPLES / f"{name}.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("name", ["case1_posting", "case2_contract", "case3_contract"])
def test_sample_image_returns_its_answer(name):
    image = (SAMPLES / f"{name}.png").read_bytes()
    kind = name.split("_")[1]
    result = MockExtractor().extract(image, "image/png", kind)
    assert result.fields == _sample(name)
    assert result.extracted_by == "mock"


def test_full_text_contains_every_quote():
    image = (SAMPLES / "case1_contract.png").read_bytes()
    result = MockExtractor().extract(image, "image/png", "contract")
    quotes = [f.quote for f in result.fields.__dict__.values() if f.quote]
    assert quotes
    assert all(q in result.full_text for q in quotes)


def test_unknown_image_falls_back_to_case1_of_same_kind():
    result = MockExtractor().extract(b"not a sample", "image/png", "posting")
    assert result.fields == _sample("case1_posting")


def test_unknown_payslip_returns_empty_fields():
    result = MockExtractor().extract(b"not a sample", "image/png", "payslip")
    assert result.fields == ConditionDoc()
    assert result.full_text == ""


def test_factory_returns_mock(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "mock")
    assert isinstance(get_extractor(), MockExtractor)
