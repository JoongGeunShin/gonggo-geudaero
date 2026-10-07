"""AI 호출부의 약속(인터페이스). 나머지 코드는 이 파일만 알고, Gemini·엔노이아 같은 구현은 모른다."""

from typing import Literal, Protocol

from pydantic import BaseModel

from app.schemas import ConditionDoc, Explanation, Finding

DocKind = Literal["posting", "contract", "payslip"]


class ExtractionResult(BaseModel):
    """문서 이미지 한 장의 추출 결과. 어떤 구현이든 이 모양으로 돌려준다."""

    full_text: str                          # OCR 원문 (인용 검증에 사용)
    fields: ConditionDoc = ConditionDoc()   # 스키마에 맞춘 추출 값


class ExtractionError(RuntimeError):
    """추출 실패. 구현(Gemini·엔노이아)과 상관없이 라우터에서 이 한 종류로 잡는다."""


class ExtractorProvider(Protocol):
    def extract(self, image_bytes: bytes, media_type: str, doc_kind: DocKind) -> ExtractionResult: ...


class OcrProvider(Protocol):
    """이미지 → 원문 글자만. 인용 검증의 기준 원문을 어디서 얻을지 바꿔 끼우는 자리.

    1단계(MVP): 별도 OCR 없이 ExtractionResult.full_text(추출과 같은 Gemini 호출)를 기준으로 쓴다.
    2단계: 이 인터페이스로 OCR을 따로 호출해 그 원문으로 검증한다 (같은 모델끼리의 일관성 검사 한계 보완).
    3단계: Tesseract 같은 독립 OCR 구현을 끼운다.
    """

    def read_text(self, image_bytes: bytes, media_type: str) -> str: ...


class ExplanationError(RuntimeError):
    """설명 생성 실패. 판정 결과는 이미 있으므로 대조 흐름을 멈추지 않고 고정 문구로 대신한다."""


class ExplainerProvider(Protocol):
    """판정 결과(findings)만 받아 쉬운 말 설명과 질문으로 바꾼다. 새로 판단하지 않는다."""

    def explain(self, findings: list[Finding]) -> Explanation: ...
