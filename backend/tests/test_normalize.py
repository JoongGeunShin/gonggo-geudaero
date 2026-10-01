import pytest

from app.rules.normalize import monthly_paid_hours


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
