"""근로조건 값을 판정 규칙이 비교할 수 있는 공통 단위(주·월 시간, 월 임금, 시급)로 바꾸는 함수들."""

from app.schemas import ConditionDoc

WEEKS_PER_MONTH = 4.345  # 365일 / 7일 / 12개월


def _hours_between(start, end, break_min):
    """"HH:MM" 두 개 사이의 근무시간(휴게 제외). 계산할 수 없으면 None."""
    if not start or not end:
        return None
    sh, sm = map(int, start.split(":"))
    eh, em = map(int, end.split(":"))
    mins = (eh * 60 + em) - (sh * 60 + sm) - (break_min or 0)
    return mins / 60 if mins > 0 else None  # 자정을 넘기는 야간 근무는 아직 미지원


def weekly_hours(doc: ConditionDoc):
    """주 소정근로시간: 문서에 숫자가 있으면 그 값, 없으면 시작·종료·휴게·근무일수로 계산."""
    wh = doc.weekly_hours.value
    if isinstance(wh, (int, float)):
        return float(wh)
    start = doc.start_time.value
    brk = doc.break_minutes.value
    brk = int(brk) if isinstance(brk, (int, float)) else (60 if start else 0)  # 적혀 있지 않으면 60분 가정
    daily = _hours_between(start, doc.end_time.value, brk)
    days = doc.work_days_per_week.value
    if daily and isinstance(days, (int, float)):
        return round(daily * days, 1)
    return None


def monthly_paid_hours(wh):
    """월 유급 소정근로시간(주휴 포함). 주 40시간이면 약 209시간."""
    if not wh:
        return None
    weekly_holiday = wh / 5 if wh >= 15 else 0  # 주 15시간 이상이면 주휴 발생
    return (min(wh, 40) + min(weekly_holiday, 8)) * WEEKS_PER_MONTH


def monthly_wage(doc: ConditionDoc, use_min=True):
    """임금을 월 단위로 환산. 범위 공고는 기본으로 최저액, use_min=False면 최고액."""
    w = doc.wage.value or {}
    t = w.get("type")
    amt = w.get("amount_min" if use_min else "amount_max") or w.get("amount_min")
    if not t or t == "비공개" or not amt:
        return None
    if t == "월급":
        return amt
    if t == "연봉":
        return amt / 12
    if t == "시급":
        hrs = monthly_paid_hours(weekly_hours(doc))
        return amt * hrs if hrs else None
    if t == "일급":
        days = doc.work_days_per_week.value
        return amt * days * WEEKS_PER_MONTH if isinstance(days, (int, float)) else None
    return None
