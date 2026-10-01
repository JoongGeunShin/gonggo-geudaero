"""공고 ↔ 계약서 판정 규칙 엔진.

규칙마다 작은 함수(check_*)로 나누고, 각 함수는 (공고, 계약서)를 받아 Finding 목록을 돌려준다.
판정은 전부 코드가 하고, LLM은 쓰지 않는다.
"""

from app.rules.normalize import base_hourly, monthly_wage, weekly_hours
from app.schemas import ConditionDoc, Finding

RED, AMBER, YELLOW, GRAY, GREEN = "불리 변경", "법 기준 확인", "누락", "모호", "동일·유리"

# 연도별 최저시급 — Phase 4-A에서 공공데이터포털 '고용노동부_연도별 최저임금' CSV로 교체
MIN_WAGE = {2025: 10030, 2026: 10320}
YEAR = 2026


def _quote(doc: ConditionDoc, key):
    return getattr(doc, key).quote if key else None


def _finding(level, item, message, posting, contract, p_key=None, c_key=None, basis=""):
    """p_key/c_key 항목의 원문 인용을 붙여 Finding 생성. c_key를 생략하면 p_key와 같은 항목."""
    return Finding(level=level, item=item, message=message,
                   posting_quote=_quote(posting, p_key),
                   contract_quote=_quote(contract, c_key or p_key),
                   basis=basis)


def _hours_key(doc: ConditionDoc):
    """근로시간 인용 위치: 주 근로시간이 적혀 있으면 그 문장, 없으면 출퇴근 시각 문장."""
    return "weekly_hours" if doc.weekly_hours.quote else "start_time"


# --- 1) 고용형태 ---

def check_employment_type(posting, contract):
    pe, ce = posting.employment_type.value, contract.employment_type.value
    if pe == "정규직" and ce and ce != "정규직":
        return [_finding(RED, "고용형태", f"공고 '{pe}' → 계약서 '{ce}'", posting, contract, "employment_type")]
    if pe and ce and pe != ce:
        return [_finding(GRAY, "고용형태", f"공고 '{pe}' / 계약서 '{ce}' 표현이 다름 — 확인 필요",
                         posting, contract, "employment_type")]
    return []


# --- 2) 수습 신설 ---

def check_probation_added(posting, contract):
    pp, cp = posting.probation.value or {}, contract.probation.value or {}
    if cp.get("exists") and not pp.get("exists"):
        return [_finding(RED, "수습", "공고에 없던 수습 기간이 계약서에 있음", posting, contract, "probation")]
    return []


# --- 3) 수습 감액 요건 ---

def check_probation_pay_cut(posting, contract):
    cp = contract.probation.value or {}
    rate = cp.get("pay_rate_percent")
    if not (cp.get("exists") and rate and rate < 100):
        return []
    violated = []
    period = contract.contract_period_months.value
    if isinstance(period, (int, float)) and period < 12:
        violated.append("계약기간 1년 미만")
    if (cp.get("months") or 0) > 3:
        violated.append("수습 3개월 초과")
    msg = f"수습 급여 {rate}% — 감액은 1년 이상 계약·수습 3개월 이내·단순노무 제외일 때만 가능"
    if violated:
        msg += f" (해당 소지: {', '.join(violated)})"
    return [_finding(AMBER, "수습 감액", msg, posting, contract, c_key="probation",
                     basis="최저임금법 제5조②, 같은 법 시행령 제3조")]


# --- 4) 근무일·근로시간 ---

def check_work_days(posting, contract):
    pd, cd = posting.work_days_per_week.value, contract.work_days_per_week.value
    if isinstance(pd, (int, float)) and isinstance(cd, (int, float)) and cd > pd:
        return [_finding(RED, "근무일", f"주 {pd}일 → 주 {cd}일", posting, contract, "work_days_per_week")]
    return []


def check_weekly_hours(posting, contract):
    pw, cw = weekly_hours(posting), weekly_hours(contract)
    if pw and cw and cw > pw:
        return [_finding(RED, "근로시간", f"주 {pw}시간 → 주 {cw}시간", posting, contract,
                         _hours_key(posting), _hours_key(contract))]
    return []


# --- 5) 포괄임금 신설 ---

def check_comprehensive_wage(posting, contract):
    pcw, ccw = posting.comprehensive_wage.value or {}, contract.comprehensive_wage.value or {}
    if ccw.get("included") and not pcw.get("included"):
        hours = ccw.get("overtime_hours_per_month")
        detail = f"(연장 {hours}시간 포함) " if hours else ""
        return [_finding(RED, "포괄임금", f"공고에 없던 포괄임금 {detail}신설", posting, contract, "comprehensive_wage")]
    return []


# --- 6) 임금 감소 ---

def check_monthly_wage(posting, contract):
    pm, cm = monthly_wage(posting), monthly_wage(contract)
    if pm is None:
        return [_finding(GRAY, "임금", "공고에 임금 기준이 없어 비교 불가 — 확인 질문으로 전환", posting, contract, "wage")]
    if cm is not None and cm < pm:
        return [_finding(RED, "임금(월 환산)", f"공고 하한 {pm:,.0f}원 → 계약서 {cm:,.0f}원", posting, contract, "wage")]
    return []


def check_base_hourly(posting, contract):
    ph, ch = base_hourly(posting), base_hourly(contract)
    if ph and ch and ch < ph * 0.99:  # 1% 미만 차이는 반올림 오차로 보고 무시
        c_key = "comprehensive_wage" if contract.comprehensive_wage.quote else "wage"
        return [_finding(RED, "임금(기본 시급)", f"연장수당 분리 후 기본 시급 {ph:,.0f}원 → {ch:,.0f}원",
                         posting, contract, "wage", c_key)]
    return []


# --- 7) 최저임금 ---

def check_minimum_wage(posting, contract):
    ch, mw = base_hourly(contract), MIN_WAGE.get(YEAR)
    if ch and mw and round(ch, 2) < mw:  # 소수점 계산 오차로 최저시급 '정확히'가 미달 처리되지 않도록
        return [_finding(AMBER, "최저임금", f"기본 시급 약 {ch:,.0f}원 < {YEAR}년 최저시급 {mw:,}원",
                         posting, contract, c_key="wage", basis="최저임금법 제6조")]
    return []


# --- 8) 근무지 ---

def check_workplace(posting, contract):
    pl, cl = posting.workplace.value, contract.workplace.value
    if not (pl and cl):
        return []
    p, c = pl.replace(" ", ""), cl.replace(" ", "")
    if p not in c and c not in p:  # 한쪽이 다른 쪽을 포함하면(더 자세한 표기) 같은 곳으로 봄
        return [_finding(GRAY, "근무지", f"'{pl}' / '{cl}' — 같은 곳인지 확인 필요", posting, contract, "workplace")]
    return []


# --- 9) 위약·손해배상 ---

def check_penalty_clause(posting, contract):
    if contract.penalty_or_damages_clause.value:
        return [_finding(AMBER, "위약·손해배상 예정", "중도 퇴사 시 금액을 물게 하는 조항이 있음",
                         posting, contract, c_key="penalty_or_damages_clause", basis="근로기준법 제20조")]
    return []


# --- 10) 필수 명시사항 누락 (계약서) ---

REQUIRED_ITEMS = {"wage": "임금", "pay_day": "임금 지급일", "holidays": "휴일"}


def check_required_items(posting, contract):
    out = []
    basis = "근로기준법 제17조"
    if not weekly_hours(contract):
        out.append(Finding(level=YELLOW, item="소정근로시간", message="계약서에 근로시간을 확인할 수 없음", basis=basis))
    for key, name in REQUIRED_ITEMS.items():
        if not getattr(contract, key).value:
            out.append(Finding(level=YELLOW, item=name, message="계약서에 기재 없음", basis=basis))
    if not contract.annual_leave.value:
        hc = contract.headcount.value
        note = "" if isinstance(hc, (int, float)) and hc >= 5 else " (상시 5인 이상 사업장인 경우)"
        out.append(Finding(level=YELLOW, item="연차유급휴가", message="계약서에 기재 없음" + note,
                           basis="근로기준법 제17조·제60조"))
    return out


# --- 전체 실행 ---

RULES = [
    check_employment_type,
    check_probation_added,
    check_probation_pay_cut,
    check_work_days,
    check_weekly_hours,
    check_comprehensive_wage,
    check_monthly_wage,
    check_base_hourly,
    check_minimum_wage,
    check_workplace,
    check_penalty_clause,
    check_required_items,
]


def compare(posting: ConditionDoc, contract: ConditionDoc) -> list[Finding]:
    """모든 규칙을 차례로 돌리고, 불리 변경·법 기준 확인이 하나도 없으면 '동일·유리'를 덧붙인다."""
    findings = [f for rule in RULES for f in rule(posting, contract)]
    # 11) 아무 문제 없음
    if not any(f.level in (RED, AMBER) for f in findings):
        findings.append(Finding(level=GREEN, item="전체", message="공고 대비 불리하게 바뀐 조건을 찾지 못했음"))
    return findings
