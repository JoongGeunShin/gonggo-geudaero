import pytest

from app.rules.normalize import monthly_paid_hours, weekly_hours
from app.schemas import ConditionDoc, ExtractedField


def make_doc(**values):
    """테스트용 문서: make_doc(start_time="09:00") → start_time.value만 채운 ConditionDoc"""
    return ConditionDoc(**{key: ExtractedField(value=v) for key, v in values.items()})


# --- monthly_paid_hours: 주 소정근로시간 → 월 유급시간(주휴 포함) ---

def test_40h_week_is_about_209_hours():
    assert round(monthly_paid_hours(40)) == 209


def test_under_15h_has_no_weekly_holiday():
    assert monthly_paid_hours(14) == 14 * 4.345


def test_exactly_15h_gets_weekly_holiday():
    # 경계값: 15시간 "이상"부터 주휴 발생 → 15 + 15/5 = 18시간/주
    assert monthly_paid_hours(15) == pytest.approx(18 * 4.345)


def test_over_40h_is_capped_at_40_plus_8():
    # 연장근로는 소정근로가 아님: 소정 40시간 + 주휴 8시간이 상한
    assert monthly_paid_hours(52) == pytest.approx(48 * 4.345)


@pytest.mark.parametrize("wh", [None, 0])
def test_unknown_hours_returns_none(wh):
    assert monthly_paid_hours(wh) is None


# --- weekly_hours: 문서 → 주 소정근로시간 ---

def test_written_weekly_hours_wins_over_calculation():
    # case1 계약서: 격주 토요일이 4시간뿐이라 계산(8h × 5.5일 = 44h)보다 적힌 42h가 정확
    doc = make_doc(weekly_hours=42, start_time="09:00", end_time="18:00",
                   break_minutes=60, work_days_per_week=5.5)
    assert weekly_hours(doc) == 42.0


def test_calculated_from_time_range():
    doc = make_doc(start_time="09:00", end_time="18:00", break_minutes=60, work_days_per_week=5)
    assert weekly_hours(doc) == 40.0


def test_explicit_zero_break_is_not_deducted():
    # 경계값: 휴게시간 "0분"이라고 적힌 경우는 빼지 않음
    doc = make_doc(start_time="09:00", end_time="13:00", break_minutes=0, work_days_per_week=5)
    assert weekly_hours(doc) == 20.0


def test_missing_break_assumes_60_minutes():
    doc = make_doc(start_time="09:00", end_time="18:00", work_days_per_week=5)
    assert weekly_hours(doc) == 40.0


def test_result_is_rounded_to_one_decimal():
    # 4시간 20분 × 5일 = 21.666... → 21.7
    doc = make_doc(start_time="09:00", end_time="13:20", break_minutes=0, work_days_per_week=5)
    assert weekly_hours(doc) == 21.7


@pytest.mark.parametrize("values", [
    {"start_time": "09:00", "end_time": "18:00", "break_minutes": 60},                 # 근무일수 없음
    {"start_time": "09:00", "break_minutes": 60, "work_days_per_week": 5},             # 종료시간 없음
    {"start_time": "22:00", "end_time": "06:00", "break_minutes": 60, "work_days_per_week": 5},  # 야간(자정 넘김): 아직 미지원
])
def test_cannot_calculate_returns_none(values):
    assert weekly_hours(make_doc(**values)) is None
