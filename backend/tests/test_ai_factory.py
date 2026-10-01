import pytest

from app.ai import get_extractor
from app.ai.base import ExtractionResult
from app.config import settings


def test_unknown_provider_raises(monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "nope")
    with pytest.raises(ValueError, match="nope"):
        get_extractor()


def test_extraction_result_defaults_to_empty_fields():
    result = ExtractionResult(full_text="시급 10,320원")
    assert result.fields.wage.value is None
