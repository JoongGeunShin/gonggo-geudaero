import pytest

from app.ai.prompts import EXTRACT_PROMPT_VERSION, load_prompt
from app.schemas import ConditionDoc


def test_extract_prompt_mentions_every_schema_field():
    prompt = load_prompt(EXTRACT_PROMPT_VERSION)
    missing = [name for name in ConditionDoc.model_fields if f'"{name}"' not in prompt]
    assert missing == []


def test_unknown_prompt_raises():
    with pytest.raises(FileNotFoundError):
        load_prompt("nope")
