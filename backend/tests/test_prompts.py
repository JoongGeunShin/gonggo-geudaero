import pytest

from app.ai.prompts import EXPLAIN_PROMPT_VERSION, EXTRACT_PROMPT_VERSION, load_prompt
from app.schemas import ConditionDoc, Explanation, ExplanationItem


def test_extract_prompt_mentions_every_schema_field():
    prompt = load_prompt(EXTRACT_PROMPT_VERSION)
    missing = [name for name in ConditionDoc.model_fields if f'"{name}"' not in prompt]
    assert missing == []


def test_explain_prompt_mentions_every_output_field():
    prompt = load_prompt(EXPLAIN_PROMPT_VERSION)
    names = ["items", *ExplanationItem.model_fields]
    assert [name for name in names if f'"{name}"' not in prompt] == []


def test_explain_prompt_forbids_assertive_wording():
    prompt = load_prompt(EXPLAIN_PROMPT_VERSION)
    assert "위반" in prompt and "확인이 필요합니다" in prompt


def test_explanation_defaults_to_no_items():
    assert Explanation(prompt_version="x").items == []


def test_unknown_prompt_raises():
    with pytest.raises(FileNotFoundError):
        load_prompt("nope")
