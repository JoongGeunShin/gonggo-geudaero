"""인용 검증: 추출 값의 근거(quote)가 원문(full_text)에 실제로 있는지 확인하고, 없으면 값을 버린다.

한계: MVP의 full_text도 같은 Gemini 호출이 만든 것이라 '같은 모델끼리의 일관성 검사'다 (Step 6-5 참고).
"""

import re
import unicodedata

from app.ai.base import ExtractionResult

# NFKC가 바꾸지 않는 따옴표·물결·대시를 통일
_SAME_CHARS = str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'", "〜": "~", "～": "~", "－": "-"})

SKIP_FIELDS = {"doc_type"}   # 문서 종류는 인용 없이 판단하는 값


def normalize(text: str) -> str:
    """비교용: 전각→반각, 따옴표·물결 통일, 공백·줄바꿈 전부 제거, 마스킹(*) 제거."""
    text = unicodedata.normalize("NFKC", text).translate(_SAME_CHARS)
    return re.sub(r"\s+", "", text).replace("*", "")


def _is_empty(value) -> bool:
    return value is None or value == "" or value == {}


def verify_quotes(result: ExtractionResult) -> ExtractionResult:
    """검증한 새 결과를 돌려준다 (입력은 바꾸지 않음). 버린 필드는 value=None, verification에 이유."""
    source = normalize(result.full_text)
    updates = {}
    for name, field in result.fields:
        if name in SKIP_FIELDS or _is_empty(field.value):
            continue
        if not field.quote:
            updates[name] = field.model_copy(update={"value": None, "verification": "quote_missing"})
        elif normalize(field.quote) not in source:
            updates[name] = field.model_copy(update={"value": None, "verification": "quote_not_found"})
    return result.model_copy(update={"fields": result.fields.model_copy(update=updates)})
