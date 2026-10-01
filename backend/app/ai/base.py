"""AI 호출부의 약속(인터페이스). 나머지 코드는 이 파일만 알고, Gemini·엔노이아 같은 구현은 모른다."""

from typing import Literal, Protocol

from pydantic import BaseModel

from app.schemas import ConditionDoc, Finding

DocKind = Literal["posting", "contract", "payslip"]


class ExtractionResult(BaseModel):
    """문서 이미지 한 장의 추출 결과. 어떤 구현이든 이 모양으로 돌려준다."""

    full_text: str                          # OCR 원문 (인용 검증에 사용)
    fields: ConditionDoc = ConditionDoc()   # 스키마에 맞춘 추출 값


class ExtractorProvider(Protocol):
    def extract(self, image_bytes: bytes, media_type: str, doc_kind: DocKind) -> ExtractionResult: ...


class ExplainerProvider(Protocol):
    """판정 결과를 사람이 읽을 설명으로 바꾼다 (Phase 9)."""

    def explain(self, findings: list[Finding]) -> dict: ...
