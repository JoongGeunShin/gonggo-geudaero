from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, field_validator


class ExtractedField(BaseModel):
    """문서에서 뽑은 항목 하나: 정규화된 값 + 근거가 된 원문 인용."""

    value: Any = None
    quote: Optional[str] = None
    verification: Optional[Literal["quote_not_found", "quote_missing"]] = None   # 인용 검증에서 값이 버려진 이유


class ConditionDoc(BaseModel):
    """채용공고 또는 근로계약서 한 장에서 추출한 근로조건 (test_kit/prompt_extract.md 스키마)."""

    model_config = ConfigDict(extra="forbid")

    doc_type: ExtractedField = ExtractedField()                    # 공고 | 계약서
    company: ExtractedField = ExtractedField()                     # 사업장명
    headcount: ExtractedField = ExtractedField()                   # 상시근로자 수
    employment_type: ExtractedField = ExtractedField()             # 정규직 | 계약직 | 기간제 | 파견 | 프리랜서 | 위탁 | 도급 | 기타
    contract_period_months: ExtractedField = ExtractedField()      # 계약기간(개월)
    probation: ExtractedField = ExtractedField()                   # {exists, months, pay_rate_percent}
    workplace: ExtractedField = ExtractedField()                   # 근무지
    job_duties: ExtractedField = ExtractedField()                  # 업무 내용
    work_days_per_week: ExtractedField = ExtractedField()          # 주 근무일수 (격주 토요일이면 5.5)
    work_days_desc: ExtractedField = ExtractedField()              # 근무요일 요약
    start_time: ExtractedField = ExtractedField()                  # HH:MM
    end_time: ExtractedField = ExtractedField()                    # HH:MM
    break_minutes: ExtractedField = ExtractedField()               # 휴게시간(분)
    weekly_hours: ExtractedField = ExtractedField()                # 주 소정근로시간 (문서에 적혀 있을 때만)
    wage: ExtractedField = ExtractedField()                        # {type, amount_min, amount_max}
    comprehensive_wage: ExtractedField = ExtractedField()          # {included, overtime_hours_per_month}
    allowances: ExtractedField = ExtractedField()                  # 상여·수당·식대
    pay_day: ExtractedField = ExtractedField()                     # 임금 지급일
    holidays: ExtractedField = ExtractedField()                    # 휴일 규정
    annual_leave: ExtractedField = ExtractedField()                # 연차유급휴가 규정
    social_insurance: ExtractedField = ExtractedField()            # 4대보험 적용 여부
    penalty_or_damages_clause: ExtractedField = ExtractedField()   # 위약금·교육비 반환·손해배상 조항


Level = Literal["불리 변경", "법 기준 확인", "누락", "모호", "동일·유리"]


class Finding(BaseModel):
    """공고 ↔ 계약서 비교 결과 한 건."""

    level: Level
    item: str                              # 비교 항목 (예: "수습", "임금(월 환산)")
    message: str                           # 무엇이 어떻게 달라졌는지
    posting_quote: Optional[str] = None    # 공고 쪽 근거 원문
    contract_quote: Optional[str] = None   # 계약서 쪽 근거 원문
    basis: str = ""                        # 법 조항 근거 (공고 대비 비교면 빈 값)


class ExplanationItem(BaseModel):
    """판정 결과 한 건의 쉬운 말 설명 + 사업주에게 물어볼 질문."""

    item: str        # Finding.item과 같은 값 (화면에서 이걸로 짝을 맞춘다)
    summary: str     # 쉬운 말 설명
    question: str    # 정중한 존댓말 질문 한 문장


class Explanation(BaseModel):
    """설명 단계의 결과. '동일·유리'를 뺀 판정 결과마다 하나씩."""

    prompt_version: str                 # 어떤 프롬프트(또는 고정 문구)로 만들었는지
    items: list[ExplanationItem] = []


class CompareRequest(BaseModel):
    """POST /rules/compare 요청: 추출이 끝난 공고·계약서 JSON 한 쌍."""

    posting: ConditionDoc
    contract: ConditionDoc


class PostingCreate(BaseModel):
    """POST /postings 요청: 지금은 추출 결과 JSON을 직접 넣는 수동 입력만 받는다."""

    source_type: Literal["capture", "url", "manual"] = "manual"
    source_url: Optional[str] = None
    raw_text: Optional[str] = None
    extracted_json: ConditionDoc
    company_name: Optional[str] = None
    b_no: Optional[str] = None


class PostingRead(PostingCreate):
    """저장된 공고. DB 객체(models.Posting)에서 바로 만든다."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    nts_status_json: Optional[dict] = None   # 국세청 상태조회 응답 (null = 조회 안 함 또는 확인 불가)
    extracted_by: Optional[str] = None       # mock | gemini:<모델명> (null = 수동 입력)


class ComparisonRead(BaseModel):
    """저장된 대조 결과. DB 객체(models.Comparison)에서 바로 만든다."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    posting_id: int
    document_id: int
    findings_json: list[Finding]
    explanation_json: Optional[Explanation] = None   # 설명 단계 결과 (Phase 9 이전 결과는 null)
    contract_extracted_by: Optional[str] = None      # 계약서 추출 주체: mock | gemini:<모델명>
    created_at: datetime


class BusinessCheckRequest(BaseModel):
    """POST /postings/{id}/business-check 요청."""

    b_no: str   # 사업자등록번호, 하이픈 있어도 됨

    @field_validator("b_no")
    @classmethod
    def ten_digits(cls, v: str) -> str:
        v = v.replace("-", "").strip()
        if len(v) != 10 or not v.isdigit():
            raise ValueError("사업자등록번호는 숫자 10자리")
        return v
