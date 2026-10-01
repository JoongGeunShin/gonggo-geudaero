import pytest

from app.rules.normalize import base_hourly, monthly_paid_hours, monthly_wage, weekly_hours
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


# --- monthly_wage: 임금(시급·일급·월급·연봉) → 월 임금 ---

def wage_doc(type_, amount_min, amount_max=None, **values):
    """임금 항목을 채운 문서. amount_max를 생략하면 amount_min과 같은 값(금액이 하나인 경우)."""
    wage = {"type": type_, "amount_min": amount_min,
            "amount_max": amount_min if amount_max is None else amount_max}
    return make_doc(wage=wage, **values)


def test_monthly_wage_as_is():
    assert monthly_wage(wage_doc("월급", 2_500_000)) == 2_500_000


def test_annual_wage_divided_by_12():
    assert monthly_wage(wage_doc("연봉", 30_000_000)) == 2_500_000


def test_annual_range_uses_min_by_default_and_max_on_request():
    # 경계값: "연봉 3,000~3,600만원" 같은 범위 공고 → 기본은 최저액(근로자에게 보수적으로)
    doc = wage_doc("연봉", 30_000_000, 36_000_000)
    assert monthly_wage(doc) == 2_500_000
    assert monthly_wage(doc, use_min=False) == 3_000_000


def test_missing_max_falls_back_to_min():
    doc = make_doc(wage={"type": "월급", "amount_min": 2_500_000})
    assert monthly_wage(doc, use_min=False) == 2_500_000


def test_hourly_wage_uses_monthly_paid_hours():
    # 2026 최저시급 10,320원 × 주 40시간(월 약 209시간)
    doc = wage_doc("시급", 10_320, start_time="09:00", end_time="18:00",
                   break_minutes=60, work_days_per_week=5)
    assert monthly_wage(doc) == pytest.approx(10_320 * 48 * 4.345)


def test_daily_wage_times_days():
    doc = wage_doc("일급", 100_000, work_days_per_week=5)
    assert monthly_wage(doc) == pytest.approx(100_000 * 5 * 4.345)


@pytest.mark.parametrize("doc", [
    make_doc(),                                                 # 임금 항목 자체가 없음
    make_doc(wage={"type": "비공개", "amount_min": None, "amount_max": None}),  # 경계값: "회사 내규에 따름"
    wage_doc("월급", 0),                                        # 금액 0
    wage_doc("시급", 10_320),                                   # 근무시간을 몰라 월 환산 불가
    wage_doc("일급", 100_000),                                  # 근무일수를 몰라 월 환산 불가
])
def test_cannot_calculate_wage_returns_none(doc):
    assert monthly_wage(doc) is None


# --- base_hourly: 포괄임금 속 연장근로수당을 떼어낸 기본 시급 ---

FULL_TIME = {"start_time": "09:00", "end_time": "18:00", "break_minutes": 60, "work_days_per_week": 5}
PAID_HOURS_40H = 48 * 4.345  # 주 40시간의 월 유급시간 ≈ 208.6


def test_base_hourly_without_comprehensive_wage():
    doc = wage_doc("월급", 2_500_000, **FULL_TIME)
    assert base_hourly(doc) == pytest.approx(2_500_000 / PAID_HOURS_40H)


def test_comprehensive_overtime_counts_1_5_times():
    # 월 20시간 연장근로가 포함된 포괄임금 → 분모에 20 × 1.5 = 30시간 추가
    doc = wage_doc("월급", 2_500_000, **FULL_TIME,
                   comprehensive_wage={"included": True, "overtime_hours_per_month": 20})
    assert base_hourly(doc) == pytest.approx(2_500_000 / (PAID_HOURS_40H + 30))


def test_comprehensive_not_included_is_ignored():
    doc = wage_doc("월급", 2_500_000, **FULL_TIME,
                   comprehensive_wage={"included": False, "overtime_hours_per_month": 20})
    assert base_hourly(doc) == pytest.approx(2_500_000 / PAID_HOURS_40H)


def test_comprehensive_without_hours_adds_nothing():
    # 경계값: "포괄임금"이라고만 적히고 시간 수가 없음 → 뺄 수 있는 연장근로 없음
    doc = wage_doc("월급", 2_500_000, **FULL_TIME,
                   comprehensive_wage={"included": True, "overtime_hours_per_month": None})
    assert base_hourly(doc) == pytest.approx(2_500_000 / PAID_HOURS_40H)


def test_hourly_wage_round_trips():
    # 시급 → 월 환산 → 다시 시급: 원래 시급으로 돌아와야 함
    doc = wage_doc("시급", 10_320, **FULL_TIME)
    assert base_hourly(doc) == pytest.approx(10_320)


@pytest.mark.parametrize("doc", [
    make_doc(wage={"type": "비공개", "amount_min": None, "amount_max": None}, **FULL_TIME),  # 임금 모름
    wage_doc("월급", 2_500_000),                                                          # 근무시간 모름
])
def test_cannot_calculate_base_hourly_returns_none(doc):
    assert base_hourly(doc) is None
