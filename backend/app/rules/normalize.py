"""근로조건 값을 판정 규칙이 비교할 수 있는 공통 단위(주·월 시간, 월 임금, 시급)로 바꾸는 함수들."""

WEEKS_PER_MONTH = 4.345  # 365일 / 7일 / 12개월


def monthly_paid_hours(wh):
    """월 유급 소정근로시간(주휴 포함). 주 40시간이면 약 209시간."""
    if not wh:
        return None
    weekly_holiday = wh / 5 if wh >= 15 else 0  # 주 15시간 이상이면 주휴 발생
    return (min(wh, 40) + min(weekly_holiday, 8)) * WEEKS_PER_MONTH
