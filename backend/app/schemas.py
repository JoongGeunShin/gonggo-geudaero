from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class ExtractedField(BaseModel):
    """문서에서 뽑은 항목 하나: 정규화된 값 + 근거가 된 원문 인용."""

    value: Any = None
    quote: Optional[str] = None


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
