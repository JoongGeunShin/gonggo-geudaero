"""개인정보 마스킹: 저장하기 전에 OCR 원문과 모든 인용에서 주민등록번호·휴대폰 번호·이메일을 가린다.

원본 이미지는 기본으로 저장하지 않는다 (Phase 7 업로드 API에서 사용자가 선택할 때만).
"""

import re

from app.ai.base import ExtractionResult

_PATTERNS = [
    # 주민등록번호: 앞 6자리 + (하이픈) + 성별 1~8로 시작하는 7자리. 앞뒤가 숫자면 다른 번호라 제외.
    (re.compile(r"(?<!\d)\d{6}\s*-?\s*[1-8]\d{6}(?!\d)"), "******-*******"),
    # 휴대폰: 010·011·016~019, 구분자는 하이픈·공백·점 허용
    (re.compile(r"(?<!\d)01[016789][\s.-]*\d{3,4}[\s.-]*\d{4}(?!\d)"), "***-****-****"),
    (re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+"), "***@***"),
]


def mask_text(text: str | None) -> str | None:
    if not text:
        return text
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def mask_result(result: ExtractionResult) -> ExtractionResult:
    """full_text와 모든 필드의 quote를 가린 새 결과 (입력은 바꾸지 않음)."""
    masked_fields = {
        name: field.model_copy(update={"quote": mask_text(field.quote)})
        for name, field in result.fields
        if field.quote
    }
    return result.model_copy(update={
        "full_text": mask_text(result.full_text),
        "fields": result.fields.model_copy(update=masked_fields),
    })
