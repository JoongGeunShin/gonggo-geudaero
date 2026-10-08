from app.rules import engine
from app.rules.engine import AMBER, GRAY, GREEN, RED, YELLOW, compare
from tests.factories import FULL_TIME, make_doc, wage_doc

# 필수 명시사항이 모두 적힌 계약서 기본값 (누락 규칙이 다른 테스트를 방해하지 않도록)
COMPLETE = {**FULL_TIME, "pay_day": "매월 10일", "holidays": "매주 일요일", "annual_leave": "근로기준법에 따름"}


def items(findings, level=None):
    """결과에서 (등급, 항목) 쌍만 뽑기. level을 주면 그 등급만."""
    return {(f.level, f.item) for f in findings if level is None or f.level == level}


# --- 1) 고용형태 ---

def test_regular_to_non_regular_is_unfavorable():
    found = engine.check_employment_type(make_doc(employment_type="정규직"), make_doc(employment_type="계약직"))
    assert items(found) == {(RED, "고용형태")}


def test_different_employment_wording_is_ambiguous():
    found = engine.check_employment_type(make_doc(employment_type="계약직"), make_doc(employment_type="파견"))
    assert items(found) == {(GRAY, "고용형태")}


def test_fixed_term_and_contract_worker_are_the_same():
    # 표준 양식 제목이 '기간제 근로자 표준근로계약서'라 공고 '계약직' ↔ 계약서 '기간제'는 흔하다 (Phase 10 평가에서 발견)
    assert engine.check_employment_type(make_doc(employment_type="계약직"), make_doc(employment_type="기간제")) == []
    assert engine.check_employment_type(make_doc(employment_type="기간제"), make_doc(employment_type="계약직")) == []


def test_same_employment_type_is_fine():
    assert engine.check_employment_type(make_doc(employment_type="정규직"), make_doc(employment_type="정규직")) == []


def test_findings_carry_quotes_from_both_documents():
    posting = make_doc(employment_type="정규직")
    contract = make_doc(employment_type="계약직")
    posting.employment_type.quote = "고용형태: 정규직"
    contract.employment_type.quote = "계약기간 1년"
    f = engine.check_employment_type(posting, contract)[0]
    assert (f.posting_quote, f.contract_quote) == ("고용형태: 정규직", "계약기간 1년")


# --- 2) 수습 신설 ---

def test_probation_added_after_posting():
    found = engine.check_probation_added(make_doc(), make_doc(probation={"exists": True, "months": 3}))
    assert items(found) == {(RED, "수습")}


def test_probation_already_in_posting_is_fine():
    prob = {"exists": True, "months": 3}
    assert engine.check_probation_added(make_doc(probation=prob), make_doc(probation=prob)) == []


# --- 3) 수습 감액 요건 ---

def test_probation_pay_cut_needs_legal_check():
    contract = make_doc(probation={"exists": True, "months": 3, "pay_rate_percent": 90})
    found = engine.check_probation_pay_cut(make_doc(), contract)
    assert items(found) == {(AMBER, "수습 감액")}
    assert "최저임금법 제5조" in found[0].basis


def test_probation_pay_cut_lists_violated_conditions():
    contract = make_doc(contract_period_months=6, probation={"exists": True, "months": 4, "pay_rate_percent": 90})
    msg = engine.check_probation_pay_cut(make_doc(), contract)[0].message
    assert "계약기간 1년 미만" in msg and "수습 3개월 초과" in msg


def test_probation_at_full_pay_is_fine():
    contract = make_doc(probation={"exists": True, "months": 3, "pay_rate_percent": 100})
    assert engine.check_probation_pay_cut(make_doc(), contract) == []


# --- 4) 근무일·근로시간 ---

def test_more_work_days_is_unfavorable():
    found = engine.check_work_days(make_doc(work_days_per_week=5), make_doc(work_days_per_week=5.5))
    assert items(found) == {(RED, "근무일")}


def test_fewer_work_days_is_fine():
    assert engine.check_work_days(make_doc(work_days_per_week=5), make_doc(work_days_per_week=4)) == []


def test_longer_weekly_hours_is_unfavorable():
    found = engine.check_weekly_hours(make_doc(**FULL_TIME), make_doc(weekly_hours=42))
    assert items(found) == {(RED, "근로시간")}


def test_unknown_hours_are_not_compared():
    assert engine.check_weekly_hours(make_doc(), make_doc(weekly_hours=42)) == []


# --- 5) 포괄임금 신설 ---

def test_comprehensive_wage_added_after_posting():
    contract = make_doc(comprehensive_wage={"included": True, "overtime_hours_per_month": 20})
    found = engine.check_comprehensive_wage(make_doc(), contract)
    assert items(found) == {(RED, "포괄임금")}
    assert "20시간" in found[0].message


# --- 6) 임금 감소 ---

def test_lower_monthly_wage_is_unfavorable():
    found = engine.check_monthly_wage(wage_doc("월급", 2_800_000), wage_doc("월급", 2_500_000))
    assert items(found) == {(RED, "임금(월 환산)")}


def test_contract_within_posting_range_is_fine():
    # 경계값: 공고 "연봉 3,000~3,600만" → 계약 3,000만은 범위 하한이라 불리 아님
    assert engine.check_monthly_wage(wage_doc("연봉", 30_000_000, 36_000_000), wage_doc("연봉", 30_000_000)) == []


def test_undisclosed_posting_wage_is_ambiguous():
    posting = make_doc(wage={"type": "비공개", "amount_min": None, "amount_max": None})
    found = engine.check_monthly_wage(posting, wage_doc("월급", 2_500_000))
    assert items(found) == {(GRAY, "임금")}


def test_hidden_overtime_lowers_base_hourly():
    # case1 유형: 월급은 같지만 계약서에 포괄 연장 20시간이 숨어 있음
    posting = wage_doc("월급", 2_500_000, **FULL_TIME)
    contract = wage_doc("월급", 2_500_000, **FULL_TIME,
                        comprehensive_wage={"included": True, "overtime_hours_per_month": 20})
    assert engine.check_monthly_wage(posting, contract) == []
    assert items(engine.check_base_hourly(posting, contract)) == {(RED, "임금(기본 시급)")}


def test_base_hourly_difference_under_1_percent_is_ignored():
    posting = wage_doc("시급", 10_500, **FULL_TIME)
    contract = wage_doc("시급", 10_450, **FULL_TIME)  # 약 0.5% 차이 → 반올림 오차 수준
    assert engine.check_base_hourly(posting, contract) == []


# --- 7) 최저임금 ---

def test_below_minimum_wage_needs_legal_check():
    found = engine.check_minimum_wage(make_doc(), wage_doc("시급", 10_000, **FULL_TIME))
    assert items(found) == {(AMBER, "최저임금")}
    assert found[0].basis == "최저임금법 제6조"


def test_exactly_minimum_wage_is_fine():
    # 경계값: 최저시급 "정확히"는 미달이 아님
    contract = wage_doc("시급", engine.MIN_WAGE[engine.YEAR], **FULL_TIME)
    assert engine.check_minimum_wage(make_doc(), contract) == []


# --- 8) 근무지 ---

def test_more_detailed_workplace_is_fine():
    assert engine.check_workplace(make_doc(workplace="경기 화성시"), make_doc(workplace="경기 화성시 본사")) == []


def test_different_workplace_is_ambiguous():
    found = engine.check_workplace(make_doc(workplace="서울 강남구"), make_doc(workplace="경기 화성시"))
    assert items(found) == {(GRAY, "근무지")}


# --- 9) 위약·손해배상 ---

def test_penalty_clause_needs_legal_check():
    contract = make_doc(penalty_or_damages_clause="1년 내 퇴사 시 교육비 반환")
    found = engine.check_penalty_clause(make_doc(), contract)
    assert items(found) == {(AMBER, "위약·손해배상 예정")}
    assert found[0].basis == "근로기준법 제20조"


# --- 10) 필수 명시사항 누락 ---

def test_complete_contract_has_no_missing_items():
    contract = wage_doc("월급", 2_500_000, **COMPLETE, headcount=10)
    assert engine.check_required_items(make_doc(), contract) == []


def test_missing_items_are_reported():
    found = engine.check_required_items(make_doc(), make_doc())
    assert {f.item for f in found} == {"소정근로시간", "임금", "임금 지급일", "휴일", "연차유급휴가"}
    assert all(f.level == YELLOW for f in found)


def test_annual_leave_note_depends_on_headcount():
    # 연차는 상시 5인 이상만 의무 → 인원을 모르면 단서를 붙임
    no_leave = {k: v for k, v in COMPLETE.items() if k != "annual_leave"}
    unknown = engine.check_required_items(make_doc(), wage_doc("월급", 2_500_000, **no_leave))
    five = engine.check_required_items(make_doc(), wage_doc("월급", 2_500_000, **no_leave, headcount=5))
    assert "5인 이상" in unknown[0].message
    assert "5인 이상" not in five[0].message


# --- 11) 전체: 문제 없음 ---

def test_identical_documents_are_all_fine():
    doc = wage_doc("월급", 2_500_000, **COMPLETE, employment_type="정규직", workplace="경기 화성시")
    assert items(compare(doc, doc)) == {(GREEN, "전체")}


def test_only_missing_items_still_counts_as_fine():
    # 누락·모호만 있고 '불리 변경'·'법 기준 확인'이 없으면 동일·유리도 함께 표시
    found = compare(make_doc(), make_doc())
    assert (GREEN, "전체") in items(found)
    assert not items(found, RED) and not items(found, AMBER)


def test_unfavorable_change_hides_all_fine():
    found = compare(wage_doc("월급", 2_800_000, **COMPLETE), wage_doc("월급", 2_500_000, **COMPLETE))
    assert (GREEN, "전체") not in items(found)
