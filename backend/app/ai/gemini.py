"""Gemini 추출기: 이미지 한 장을 한 번 호출해서 ① OCR 원문(full_text)과 ② 스키마에 맞춘 fields를 같이 받는다.

무료 티어 입력은 Google 제품 개선에 쓰일 수 있으므로 실제 계약서는 넣지 말고 합성 샘플만 쓸 것.
"""

import time
from typing import Callable

import httpx
from google import genai
from google.genai import errors, types
from pydantic import ValidationError

from app.ai.base import DocKind, ExtractionResult
from app.ai.prompts import EXTRACT_PROMPT_VERSION, load_prompt
from app.schemas import ConditionDoc

OCR_ONLY_PROMPT = ("이 문서 이미지의 모든 글자를 위에서 아래로, 줄바꿈까지 그대로 옮겨 적어줘. "
                   "표는 한 행을 한 줄로 쓰고 칸 사이는 ' | '로 구분해. 설명은 쓰지 마.")
DOC_KIND_LABEL ={"posting": "채용공고", "contract": "근로계약서", "payslip": "임금명세서"}

RETRYABLE_CODES = {429, 500, 503}   # 한도 초과·일시적 서버 오류만 다시 시도
FIRST_WAIT_SECONDS = 10
TIMEOUT_MS = 120_000   # 이미지 한 장 추출에 1분 넘게 걸리기도 한다


def _nullable(schema: dict) -> dict:
    return {"anyOf": [schema, {"type": "null"}]}


_NUM = {"type": "number"}
_STR = {"type": "string"}
_BOOL = {"type": "boolean"}

# 항목별 value 타입. 엔진이 dict로 읽는 항목(wage 등)은 반드시 object로 받도록 고정한다.
_VALUE_SCHEMAS = {
    "headcount": _NUM,
    "contract_period_months": _NUM,
    "work_days_per_week": _NUM,
    "break_minutes": _NUM,
    "weekly_hours": _NUM,
    "probation": {"type": "object", "properties": {
        "exists": _BOOL, "months": _nullable(_NUM), "pay_rate_percent": _nullable(_NUM)}},
    "wage": {"type": "object", "properties": {
        "type": {"type": "string", "enum": ["월급", "연봉", "시급", "일급", "비공개"]},
        "amount_min": _nullable(_NUM), "amount_max": _nullable(_NUM)}},
    "comprehensive_wage": {"type": "object", "properties": {
        "included": _BOOL, "overtime_hours_per_month": _nullable(_NUM)}},
}


def response_schema() -> dict:
    """Gemini 구조화 출력용 스키마.

    pydantic의 model_json_schema()를 그대로 넘기면 value: Any가 타입 없는 스키마({})가 되어 400이 난다.
    그래서 항목마다 value 타입을 명시한 스키마를 따로 만든다. 받은 응답은 다시 ExtractionResult로 검증한다.
    """
    fields = {
        name: {"type": "object", "properties": {
            "value": _nullable(_VALUE_SCHEMAS.get(name, _STR)),
            "quote": _nullable(_STR),
        }}
        for name in ConditionDoc.model_fields
    }
    return {
        "type": "object",
        "properties": {"full_text": _STR, "fields": {"type": "object", "properties": fields}},
        "required": ["full_text", "fields"],
    }


class ExtractionError(RuntimeError):
    """추출 실패를 라우터에서 한 종류로 잡을 수 있게 감싼 에러."""


class GeminiExtractor:
    def __init__(self, client=None, model: str = "", api_key: str = "",
                 max_retries: int = 3, sleep: Callable[[float], None] = time.sleep):
        self.client = client or genai.Client(
            api_key=api_key, http_options=types.HttpOptions(timeout=TIMEOUT_MS))
        self.model = model
        self.max_retries = max_retries
        self.sleep = sleep
        self.prompt = load_prompt(EXTRACT_PROMPT_VERSION)

    def extract(self, image_bytes: bytes, media_type: str, doc_kind: DocKind) -> ExtractionResult:
        contents = [
            types.Part.from_bytes(data=image_bytes, mime_type=media_type),
            f"{self.prompt}\n\n이 이미지는 {DOC_KIND_LABEL[doc_kind]}다. "
            "fields의 quote는 반드시 full_text 안에 있는 글자를 그대로 옮긴다.",
        ]
        config = types.GenerateContentConfig(
            temperature=0,
            response_mime_type="application/json",
            response_json_schema=response_schema(),   # 구조화 출력: JSON만 받기
        )
        last_error: Exception | None = None
        for _ in range(2):   # 스키마에 안 맞으면 1회만 다시 요청
            text = self._call(contents, config)
            try:
                return ExtractionResult.model_validate_json(text or "")
            except ValidationError as e:
                last_error = e
        raise ExtractionError(f"Gemini 응답이 추출 스키마에 맞지 않습니다: {last_error}")

    def read_text(self, image_bytes: bytes, media_type: str) -> str:
        """OCR만 따로 호출 (OcrProvider). MVP에서는 extract()의 full_text를 쓰고, 2단계에서 이걸로 바꾼다."""
        contents = [types.Part.from_bytes(data=image_bytes, mime_type=media_type), OCR_ONLY_PROMPT]
        return self._call(contents, types.GenerateContentConfig(temperature=0)) or ""

    def _call(self, contents, config) -> str | None:
        """429·5xx면 10초, 20초, 40초… 기다렸다 다시 시도 (지수 백오프)."""
        wait = FIRST_WAIT_SECONDS
        for attempt in range(self.max_retries + 1):
            try:
                return self.client.models.generate_content(
                    model=self.model, contents=contents, config=config).text
            except errors.APIError as e:
                if e.code in RETRYABLE_CODES and attempt < self.max_retries:
                    self.sleep(wait)
                    wait *= 2
                    continue
                raise ExtractionError(f"Gemini 호출 실패 ({e.code}): {e.message}") from e
            except httpx.TimeoutException as e:   # 타임아웃은 APIError가 아니라 httpx 예외로 온다
                if attempt < self.max_retries:
                    self.sleep(wait)
                    wait *= 2
                    continue
                raise ExtractionError(f"Gemini 응답 시간 초과 ({TIMEOUT_MS // 1000}초)") from e
