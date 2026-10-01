"""테스트에서 공고·계약서 문서를 짧게 만들기 위한 헬퍼."""

from app.schemas import ConditionDoc, ExtractedField

FULL_TIME = {"start_time": "09:00", "end_time": "18:00", "break_minutes": 60, "work_days_per_week": 5}
PAID_HOURS_40H = 48 * 4.345  # 주 40시간의 월 유급시간 ≈ 208.6


def make_doc(**values):
    """테스트용 문서: make_doc(start_time="09:00") → start_time.value만 채운 ConditionDoc"""
    return ConditionDoc(**{key: ExtractedField(value=v) for key, v in values.items()})


def wage_doc(type_, amount_min, amount_max=None, **values):
    """임금 항목을 채운 문서. amount_max를 생략하면 amount_min과 같은 값(금액이 하나인 경우)."""
    wage = {"type": type_, "amount_min": amount_min,
            "amount_max": amount_min if amount_max is None else amount_max}
    return make_doc(wage=wage, **values)
