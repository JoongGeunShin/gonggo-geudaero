"""Phase 10 평가용 합성 공고·계약서 40쌍 생성기.

    backend/.venv/Scripts/python eval/make_dataset.py      # 저장소 루트에서 (Pillow 필요: eval/requirements.txt)

만드는 것 (eval/data/):
    pairNN_posting.png / pairNN_contract.png   문서 이미지 (일부는 휴대폰 사진처럼 기울기·그림자·흐림)
    pairNN_posting.json / pairNN_contract.json 정답 추출값 (ConditionDoc, 인용은 원문 그대로)
    pairNN_posting.txt / pairNN_contract.txt   이미지에 그린 원문 (OCR 정확도 비교용)
    answer_key.json                            쌍마다 변형 종류와 엔진이 내야 할 경고 목록 (사람이 정한 정답)

answer_key의 expected_flags는 엔진 결과를 복사한 것이 아니라 변형 내용을 보고 손으로 정한 값이다.
정답 JSON을 엔진에 넣었을 때 그대로 나오는지는 backend/tests/test_eval_dataset.py가 확인한다.
"""

import json
import random
import sys
from copy import deepcopy
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.schemas import ConditionDoc  # noqa: E402

OUT = Path(__file__).resolve().parent / "data"

FONT = "C:/Windows/Fonts/malgun.ttf"
FONT_BOLD = "C:/Windows/Fonts/malgunbd.ttf"
WIDTH, HEIGHT, MARGIN = 1240, 1400, 64

R, A, Y, G = "불리 변경", "법 기준 확인", "누락", "모호"


# ---------------------------------------------------------------- 기본 일자리 8종

JOBS = {
    "J1": dict(company="(주)가나정밀(모의)", title="생산관리 사무원 채용", emp="정규직", period=None,
               workplace="경기 화성시 ○○로", duties="생산관리 사무보조, 서류 정리",
               days=5, days_desc="월~금", start="09:00", end="18:00", brk=60,
               wage=("월급", 2500000, 2500000), style="table"),
    "J2": dict(company="(주)다라물류(모의)", title="물류센터 재고관리 계약직", emp="계약직", period=6,
               workplace="경기 시흥시 정왕동", duties="입출고 관리 및 전산 입력",
               days=5, days_desc="월~금", start="09:00", end="18:00", brk=60,
               wage=("월급", 2400000, 2400000), style="table"),
    "J3": dict(company="마바베이커리(모의)", title="주말 매장 판매 아르바이트", emp="아르바이트", period=None,
               workplace="서울 마포구 ○○동 매장", duties="빵 진열 및 계산",
               days=3, days_desc="토, 일, 월", start="10:00", end="15:00", brk=30,
               wage=("시급", 11000, 11000), style="table"),
    "J4": dict(company="(주)사아소프트(모의)", title="웹 서비스 운영 담당자", emp="정규직", period=None,
               workplace="서울 강남구 역삼동", duties="웹 서비스 운영 및 고객 문의 대응",
               days=5, days_desc="월~금", start="10:00", end="19:00", brk=60,
               wage=("연봉", 36000000, 36000000), style="list"),
    "J5": dict(company="자차카페(모의)", title="평일 오후 카페 바리스타", emp="아르바이트", period=None,
               workplace="부산 해운대구 ○○로 매장", duties="음료 제조 및 매장 관리",
               days=5, days_desc="월~금", start="14:00", end="20:00", brk=30,
               wage=("시급", 10800, 10800), style="table"),
    "J6": dict(company="(주)타파건설(모의)", title="현장 공무 담당 정규직", emp="정규직", period=None,
               workplace="대전 유성구 ○○동 현장사무소", duties="현장 공무 및 자재 관리",
               days=5, days_desc="월~금", start="08:00", end="17:00", brk=60,
               wage=("월급", 3000000, 3500000), style="table"),
    "J7": dict(company="하늘요양원(모의)", title="요양보호사 계약직 모집", emp="계약직", period=12,
               workplace="광주 북구 ○○로", duties="입소 어르신 생활 지원",
               days=5, days_desc="월~금", start="09:00", end="18:00", brk=60,
               wage=("월급", 2300000, 2300000), style="list"),
    "J8": dict(company="(주)푸른마트(모의)", title="매장 관리 정규직", emp="정규직", period=None,
               workplace="인천 연수구 ○○동 매장", duties="매장 진열 및 재고 관리",
               days=5, days_desc="월~금", start="09:00", end="18:00", brk=60,
               wage=("월급", 2600000, 2600000), comp=10, style="table"),
}

# 계약서에만 있는 항목의 기본값 (누락 변형이 None으로 바꾼다)
CONTRACT_DEFAULTS = dict(pay_day="매월 10일", holidays="매주 일요일", annual_leave=True, hours_line=True,
                         probation=None, comp=None, penalty=None)

PENALTIES = {
    "edu30": "근무 시작 후 3개월 이내 퇴사 시 교육비 30만원을 마지막 급여에서 공제한다.",
    "hire100": "입사 후 1년 이내 퇴사 시 채용 및 교육 비용 100만원을 회사에 배상한다.",
    "notice": "퇴사 30일 전에 알리지 않고 퇴사하는 경우 손해배상금으로 월급의 50%를 지급한다.",
}


def case(no, job, desc, variations, expected, posting=None, contract=None, photo=(False, False)):
    return dict(id=f"pair{no:02d}", job=job, desc=desc, variations=variations, expected=expected,
                posting=posting or {}, contract=contract or {}, photo_posting=photo[0], photo_contract=photo[1])


CASES = [
    # --- 동일 (오탐 확인용) ---
    case(1, "J1", "조건 동일", ["동일"], []),
    case(2, "J3", "조건 동일 (시급 아르바이트)", ["동일"], []),
    case(3, "J4", "조건 동일 (연봉, 목록형 공고)", ["동일"], []),
    case(4, "J6", "공고 범위(300만~350만)의 하한으로 계약", ["동일"], [], contract=dict(wage=("월급", 3000000, 3000000))),
    case(5, "J8", "공고에도 포괄임금이 있었음", ["동일"], [], contract=dict(comp=10)),
    case(6, "J7", "조건 동일 (계약직, 사진)", ["동일", "사진"], [], photo=(False, True)),
    # --- 임금 감액 ---
    case(7, "J1", "월급 250만 → 230만", ["임금 감액"], [(R, "임금(월 환산)"), (R, "임금(기본 시급)")],
         contract=dict(wage=("월급", 2300000, 2300000))),
    case(8, "J3", "시급 11,000 → 10,500", ["임금 감액"], [(R, "임금(월 환산)"), (R, "임금(기본 시급)")],
         contract=dict(wage=("시급", 10500, 10500))),
    case(9, "J4", "연봉 3,600만 → 3,300만 (공고 사진)", ["임금 감액", "사진"],
         [(R, "임금(월 환산)"), (R, "임금(기본 시급)")],
         contract=dict(wage=("연봉", 33000000, 33000000)), photo=(True, False)),
    case(10, "J6", "범위 하한 300만보다 낮은 280만 (사진)", ["임금 감액", "사진"],
         [(R, "임금(월 환산)"), (R, "임금(기본 시급)")],
         contract=dict(wage=("월급", 2800000, 2800000)), photo=(False, True)),
    case(11, "J5", "시급 10,800 → 10,320", ["임금 감액"], [(R, "임금(월 환산)"), (R, "임금(기본 시급)")],
         contract=dict(wage=("시급", 10320, 10320))),
    case(12, "J2", "월급 240만 → 220만 (사진)", ["임금 감액", "사진"],
         [(R, "임금(월 환산)"), (R, "임금(기본 시급)")],
         contract=dict(wage=("월급", 2200000, 2200000)), photo=(False, True)),
    # --- 수습 신설 ---
    case(13, "J1", "수습 3개월 90% 신설", ["수습 신설"], [(R, "수습"), (A, "수습 감액")],
         contract=dict(probation=(3, 90))),
    case(14, "J4", "수습 3개월 100% 신설", ["수습 신설"], [(R, "수습")], contract=dict(probation=(3, 100))),
    case(15, "J7", "계약직 12개월에 수습 3개월 90% 신설", ["수습 신설"], [(R, "수습"), (A, "수습 감액")],
         contract=dict(probation=(3, 90))),
    case(16, "J1", "공고에도 수습 3개월이 있었음", ["동일"], [],
         posting=dict(probation=(3, None)), contract=dict(probation=(3, 100))),
    case(17, "J6", "수습 6개월 80% 신설 (사진)", ["수습 신설", "사진"], [(R, "수습"), (A, "수습 감액")],
         contract=dict(probation=(6, 80)), photo=(False, True)),
    # --- 포괄임금 전환 ---
    case(18, "J1", "같은 월급에 연장 20시간 포괄 신설", ["포괄 전환"], [(R, "포괄임금"), (R, "임금(기본 시급)")],
         contract=dict(comp=20)),
    case(19, "J4", "같은 연봉에 연장 20시간 포괄 신설", ["포괄 전환"], [(R, "포괄임금"), (R, "임금(기본 시급)")],
         contract=dict(comp=20)),
    case(20, "J2", "연장 30시간 포괄 → 기본 시급이 최저임금 미달 (사진)", ["포괄 전환", "사진"],
         [(R, "포괄임금"), (R, "임금(기본 시급)"), (A, "최저임금")], contract=dict(comp=30), photo=(False, True)),
    case(21, "J6", "범위 하한 300만에 연장 10시간 포괄", ["포괄 전환"], [(R, "포괄임금"), (R, "임금(기본 시급)")],
         contract=dict(wage=("월급", 3000000, 3000000), comp=10)),
    case(22, "J7", "연장 15시간 포괄 → 최저임금 미달", ["포괄 전환"],
         [(R, "포괄임금"), (R, "임금(기본 시급)"), (A, "최저임금")], contract=dict(comp=15)),
    # --- 필수 명시사항 누락 ---
    case(23, "J1", "임금 지급일 누락", ["누락"], [(Y, "임금 지급일")], contract=dict(pay_day=None)),
    case(24, "J3", "휴일·연차 누락", ["누락"], [(Y, "휴일"), (Y, "연차유급휴가")],
         contract=dict(holidays=None, annual_leave=False)),
    case(25, "J4", "연차 누락 (사진)", ["누락", "사진"], [(Y, "연차유급휴가")],
         contract=dict(annual_leave=False), photo=(False, True)),
    case(26, "J5", "임금 지급일·휴일 누락", ["누락"], [(Y, "임금 지급일"), (Y, "휴일")],
         contract=dict(pay_day=None, holidays=None)),
    case(27, "J2", "소정근로시간 누락", ["누락"], [(Y, "소정근로시간")], contract=dict(hours_line=False)),
    # --- 고용형태 변경 ---
    case(28, "J1", "정규직 → 계약직 12개월", ["고용형태 변경"], [(R, "고용형태")],
         contract=dict(emp="계약직", period=12)),
    case(29, "J4", "정규직 → 프리랜서", ["고용형태 변경"], [(R, "고용형태")], contract=dict(emp="프리랜서")),
    case(30, "J6", "정규직 → 계약직 6개월 (사진)", ["고용형태 변경", "사진"], [(R, "고용형태")],
         contract=dict(emp="계약직", period=6), photo=(False, True)),
    # --- 근무일·근로시간 증가 ---
    case(31, "J1", "주 5일 → 주 6일 (월~토)", ["근무일·시간 증가"], [(R, "근무일"), (R, "근로시간")],
         contract=dict(days=6, days_desc="월~토")),
    case(32, "J4", "10:00~19:00 → 09:00~19:00", ["근무일·시간 증가"], [(R, "근로시간")],
         contract=dict(start="09:00")),
    case(33, "J3", "10:00~15:00 → 10:00~17:00 (공고 사진)", ["근무일·시간 증가", "사진"], [(R, "근로시간")],
         contract=dict(end="17:00"), photo=(True, False)),
    case(34, "J5", "주 5일 → 주 6일 (월~토)", ["근무일·시간 증가"], [(R, "근무일"), (R, "근로시간")],
         contract=dict(days=6, days_desc="월~토")),
    # --- 위약·손해배상 조항 ---
    case(35, "J3", "교육비 30만원 공제 조항", ["위약 조항"], [(A, "위약·손해배상 예정")],
         contract=dict(penalty="edu30")),
    case(36, "J1", "1년 내 퇴사 시 100만원 배상 조항 (사진)", ["위약 조항", "사진"], [(A, "위약·손해배상 예정")],
         contract=dict(penalty="hire100"), photo=(False, True)),
    case(37, "J4", "공고 임금 '회사 내규' + 손해배상 조항", ["위약 조항", "임금 비공개"],
         [(G, "임금"), (A, "위약·손해배상 예정")],
         posting=dict(wage=("비공개", None, None)), contract=dict(penalty="notice")),
    # --- 최저임금 미달 ---
    case(38, "J3", "공고 시급 10,320 → 계약 10,000 (최저임금 미달)", ["임금 감액", "최저임금"],
         [(R, "임금(월 환산)"), (R, "임금(기본 시급)"), (A, "최저임금")],
         posting=dict(wage=("시급", 10320, 10320)), contract=dict(wage=("시급", 10000, 10000))),
    # --- 근무지 ---
    case(39, "J2", "근무지가 다른 지역 (사진)", ["근무지 변경", "사진"], [(G, "근무지")],
         contract=dict(workplace="인천 남동구 논현동 물류센터"), photo=(False, True)),
    # --- 복합 ---
    case(40, "J1", "수습 90% + 포괄 20시간 + 연차 누락 (사진)", ["수습 신설", "포괄 전환", "누락", "사진"],
         [(R, "수습"), (A, "수습 감액"), (R, "포괄임금"), (R, "임금(기본 시급)"), (Y, "연차유급휴가")],
         contract=dict(probation=(3, 90), comp=20, annual_leave=False), photo=(False, True)),
]


# ---------------------------------------------------------------- 문구 만들기

def emp_value(emp):
    return "기타" if emp == "아르바이트" else emp


def man(won):
    return f"{won // 10000:,}만원"


def posting_wage_text(t, lo, hi):
    if t == "비공개":
        return "회사 내규에 따름"
    if t in ("월급", "연봉"):
        return f"{t} {man(lo)}" if lo == hi else f"{t} {man(lo)} ~ {man(hi)}"
    return f"{t} {lo:,}원"


def break_text(brk):
    return "1시간" if brk == 60 else f"{brk}분"


def kor_time(hhmm):
    h, m = hhmm.split(":")
    return f"{h}시 {m}분"


def field(value=None, quote=None):
    return {"value": value, "quote": quote}


def empty_doc(doc_type):
    doc = {name: field() for name in ConditionDoc.model_fields}
    doc["doc_type"] = field(doc_type)
    return doc


def build_posting(c):
    """공고 한 장: 화면에 그릴 (제목, 행 목록)과 정답 JSON."""
    doc = empty_doc("공고")
    doc["company"] = field(c["company"], c["company"])

    emp_text = c["emp"]
    if c["period"]:
        emp_text += f" ({c['period']}개월)"
        doc["contract_period_months"] = field(c["period"], emp_text)
    if c.get("probation"):
        months, _ = c["probation"]
        emp_text += f" (수습 {months}개월)"
        doc["probation"] = field({"exists": True, "months": months, "pay_rate_percent": None}, f"수습 {months}개월")
    doc["employment_type"] = field(emp_value(c["emp"]), c["emp"])

    t, lo, hi = c["wage"]
    wage_text = posting_wage_text(t, lo, hi)
    doc["wage"] = field({"type": t, "amount_min": lo, "amount_max": hi}, wage_text)
    if c.get("comp"):
        comp_text = f"월 연장근로 {c['comp']}시간분 포함 포괄임금"
        wage_text += f" ({comp_text})"
        doc["comprehensive_wage"] = field({"included": True, "overtime_hours_per_month": c["comp"]}, comp_text)

    days_text = f"주 {c['days']}일 ({c['days_desc']})"
    doc["work_days_per_week"] = field(c["days"], days_text)
    doc["work_days_desc"] = field(c["days_desc"], days_text)
    hours_text = f"{c['start']} ~ {c['end']} (휴게 {break_text(c['brk'])})"
    doc["start_time"] = field(c["start"], hours_text)
    doc["end_time"] = field(c["end"], hours_text)
    doc["break_minutes"] = field(c["brk"], f"휴게 {break_text(c['brk'])}")
    doc["workplace"] = field(c["workplace"], c["workplace"])
    doc["job_duties"] = field(c["duties"], c["duties"])
    doc["social_insurance"] = field("4대보험", "4대보험 가입")

    rows = [("고용형태", emp_text), ("임금", wage_text), ("근무요일", days_text), ("근무시간", hours_text),
            ("근무지", c["workplace"]), ("담당업무", c["duties"]), ("복리후생", "4대보험 가입")]
    meta = f"{c['company']} · 공고일 2026.09.15 · 마감 2026.09.30"
    return dict(title=c["title"], meta=meta, rows=rows, style=c["style"]), doc


def build_contract(c):
    """계약서 한 장: 화면에 그릴 문단 목록과 정답 JSON."""
    doc = empty_doc("계약서")
    doc["company"] = field(c["company"], c["company"])
    lines = [f"{c['company']}(이하 “사업주”라 함)과(와) ***(이하 “근로자”라 함)은 다음과 같이 근로계약을 체결한다."]
    items = []

    if c["period"]:
        end = {6: "2027년 3월 31일", 12: "2027년 9월 30일"}[c["period"]]
        period_text = f"2026년 10월 1일부터 {end}까지 ({c['period']}개월, {c['emp']})"
        doc["contract_period_months"] = field(c["period"], f"{c['period']}개월")
    else:
        period_text = f"2026년 10월 1일부터 (기간의 정함 없음, {c['emp']})"
    doc["employment_type"] = field(emp_value(c["emp"]), c["emp"])
    if c["probation"]:
        months, rate = c["probation"]
        prob_text = f"입사일로부터 {months}개월은 수습기간으로 하며 수습기간 중 급여는 {rate}%를 지급한다."
        period_text += f". 단, {prob_text}"
        doc["probation"] = field({"exists": True, "months": months, "pay_rate_percent": rate}, prob_text)
    items.append(("근로계약기간", period_text))

    items.append(("근무장소", c["workplace"]))
    doc["workplace"] = field(c["workplace"], c["workplace"])
    items.append(("업무의 내용", c["duties"]))
    doc["job_duties"] = field(c["duties"], c["duties"])

    if c["hours_line"]:
        brk = c["brk"]
        noon = c["start"] <= "12:00" and c["end"] >= "13:00" and brk == 60
        brk_text = "휴게시간 12:00~13:00" if noon else f"휴게시간 {brk}분"
        hours_text = f"{kor_time(c['start'])}부터 {kor_time(c['end'])}까지 ({brk_text})"
        items.append(("소정근로시간", hours_text))
        doc["start_time"] = field(c["start"], hours_text)
        doc["end_time"] = field(c["end"], hours_text)
        doc["break_minutes"] = field(brk, brk_text)

    days_text = f"매주 {c['days_desc']} 근무"
    doc["work_days_per_week"] = field(c["days"], days_text)
    doc["work_days_desc"] = field(c["days_desc"], days_text)
    if c["holidays"]:
        hol_text = f"주휴일 {c['holidays']}"
        items.append(("근무일/휴일", f"{days_text}, {hol_text}"))
        doc["holidays"] = field(c["holidays"], hol_text)
    else:
        items.append(("근무일", days_text))

    t, amount, _ = c["wage"]
    wage_text = f"{t} {amount:,}원"
    doc["wage"] = field({"type": t, "amount_min": amount, "amount_max": amount}, wage_text)
    if c["comp"]:
        comp_text = f"월 {c['comp']}시간분 연장근로수당 포함 포괄 산정"
        wage_text += f" ({comp_text})"
        doc["comprehensive_wage"] = field({"included": True, "overtime_hours_per_month": c["comp"]}, comp_text)
    if c["pay_day"]:
        pay_text = f"임금지급일 : {c['pay_day']}"
        wage_text += f" / {pay_text} / 지급방법 : 근로자 명의 예금통장에 입금"
        doc["pay_day"] = field(c["pay_day"], pay_text)
    items.append(("임금", wage_text))

    if c["annual_leave"]:
        leave_text = "근로기준법에서 정하는 바에 따라 부여함"
        items.append(("연차유급휴가", leave_text))
        doc["annual_leave"] = field("근로기준법에 따라 부여", leave_text)

    items.append(("사회보험 적용여부", "고용보험, 산재보험, 국민연금, 건강보험"))
    doc["social_insurance"] = field("4대보험", "고용보험, 산재보험, 국민연금, 건강보험")

    if c["penalty"]:
        text = PENALTIES[c["penalty"]]
        items.append(("기타", text))
        doc["penalty_or_damages_clause"] = field(text.rstrip("."), text)

    lines += [f"{i}. {name} : {body}" for i, (name, body) in enumerate(items, 1)]
    title = {"계약직": "기간제 근로자 표준근로계약서", "아르바이트": "단시간근로자 표준근로계약서"}.get(c["emp"], "표준근로계약서")
    sign = f"2026년 9월 30일   (사업주) {c['company']} 대표 *** (서명)   (근로자) *** (서명)"
    return dict(title=title, lines=lines, sign=sign), doc


# ---------------------------------------------------------------- 그리기

def font(size, bold=False):
    return ImageFont.truetype(FONT_BOLD if bold else FONT, size)


def wrap(draw, text, fnt, width):
    """픽셀 폭에 맞춰 한 글자씩 줄바꿈 (한국어는 띄어쓰기 단위가 길어 글자 단위로 자른다)."""
    lines, cur = [], ""
    for ch in text:
        if draw.textlength(cur + ch, font=fnt) > width and cur:
            lines.append(cur)
            cur = ch.lstrip()
        else:
            cur += ch
    return lines + [cur]


def render_posting(spec):
    img = Image.new("RGB", (WIDTH, HEIGHT), "white")
    d = ImageDraw.Draw(img)
    y = 56
    d.text((MARGIN, y), "고용24 · 채용정보(모의)", font=font(24, True), fill="#1d5fd1")
    y += 56
    d.text((MARGIN, y), spec["title"], font=font(38, True), fill="#222")
    y += 66
    d.text((MARGIN, y), spec["meta"], font=font(24), fill="#666")
    y += 64
    body = font(26)
    if spec["style"] == "table":
        col = 290
        for label, value in spec["rows"]:
            vlines = wrap(d, value, body, WIDTH - 2 * MARGIN - col - 40)
            h = 30 + 38 * len(vlines)
            d.rectangle([MARGIN, y, MARGIN + col, y + h], fill="#f3f4f8", outline="#bbb", width=2)
            d.rectangle([MARGIN + col, y, WIDTH - MARGIN, y + h], fill="white", outline="#bbb", width=2)
            d.text((MARGIN + 20, y + 16), label, font=font(26, True), fill="#222")
            for i, line in enumerate(vlines):
                d.text((MARGIN + col + 20, y + 16 + 38 * i), line, font=body, fill="#222")
            y += h
    else:
        d.text((MARGIN, y), "■ 모집요강", font=font(28, True), fill="#222")
        y += 56
        for label, value in spec["rows"]:
            for i, line in enumerate(wrap(d, f"· {label} : {value}", body, WIDTH - 2 * MARGIN - 20)):
                d.text((MARGIN + 20, y), line, font=body, fill="#222")
                y += 44
            y += 8
    return img


def render_contract(spec):
    img = Image.new("RGB", (WIDTH, HEIGHT), "white")
    d = ImageDraw.Draw(img)
    title_font = font(40, True)
    title = " ".join(spec["title"]) if len(spec["title"]) <= 7 else spec["title"]
    d.text(((WIDTH - d.textlength(title, font=title_font)) / 2, 60), title, font=title_font, fill="#222")
    y, body = 150, font(26)
    for para in spec["lines"]:
        for line in wrap(d, para, body, WIDTH - 2 * MARGIN):
            d.text((MARGIN, y), line, font=body, fill="#222")
            y += 42
        y += 16
    d.text((MARGIN, y + 30), spec["sign"], font=font(23), fill="#444")
    return img


def photo_effect(img, rng):
    """휴대폰 사진처럼: 어두운 바닥 위에 기울어진 종이, 한쪽 그림자, 약한 흐림."""
    angle = rng.uniform(2.0, 5.0) * rng.choice([-1, 1])
    paper = img.rotate(angle, expand=True, resample=Image.BICUBIC, fillcolor=(110, 100, 85))
    w, h = paper.size
    shade = Image.linear_gradient("L").rotate(90 * rng.choice([1, -1])).resize((w, h))
    depth = rng.uniform(0.22, 0.32)   # 그림자 진하기 (한 번만 뽑아야 줄무늬가 안 생김)
    shade = shade.point(lambda v: 255 - int(v * depth))
    dark = Image.new("RGB", (w, h), (0, 0, 0))
    paper = Image.composite(paper, dark, shade)
    paper = paper.filter(ImageFilter.GaussianBlur(rng.uniform(0.9, 1.4)))
    return paper.resize((int(w * 0.9), int(h * 0.9)), Image.BICUBIC)


def full_text_of_posting(spec):
    lines = ["고용24 · 채용정보(모의)", spec["title"], spec["meta"]]
    if spec["style"] == "list":
        lines.append("■ 모집요강")
        lines += [f"· {label} : {value}" for label, value in spec["rows"]]
    else:
        lines += [f"{label} | {value}" for label, value in spec["rows"]]
    return "\n".join(lines)


def full_text_of_contract(spec):
    return "\n".join([spec["title"], *spec["lines"], spec["sign"]])


# ---------------------------------------------------------------- 실행

def resolve(c):
    """일자리 기본값 + 공고/계약서별 변형을 합쳐 문서 두 장의 조건을 만든다."""
    job = JOBS[c["job"]]
    posting = {**deepcopy(job), **c["posting"]}
    contract = {**deepcopy(job), **CONTRACT_DEFAULTS, **c["contract"]}
    return posting, contract


def check_quotes(doc, text, name):
    """정답의 인용이 모두 원문에 그대로 들어 있어야 한다 (인용 검증을 통과하는 정답)."""
    flat = text.replace("\n", "")
    for key, f in doc.items():
        if f["quote"] and f["quote"] not in flat:
            raise AssertionError(f"{name}.{key}: 인용이 원문에 없음 — {f['quote']}")


def main():
    OUT.mkdir(exist_ok=True)
    answer_key = {}
    for c in CASES:
        posting, contract = resolve(c)
        rng = random.Random(c["id"])
        for kind, (spec, doc), render, to_text, photo in [
            ("posting", build_posting(posting), render_posting, full_text_of_posting, c["photo_posting"]),
            ("contract", build_contract(contract), render_contract, full_text_of_contract, c["photo_contract"]),
        ]:
            name = f"{c['id']}_{kind}"
            text = to_text(spec)
            check_quotes(doc, text, name)
            ConditionDoc.model_validate(doc)
            img = render(spec)
            if photo:
                img = photo_effect(img, rng)
            img.save(OUT / f"{name}.png", optimize=True)
            (OUT / f"{name}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            (OUT / f"{name}.txt").write_text(text + "\n", encoding="utf-8")
        answer_key[c["id"]] = {
            "desc": c["desc"],
            "variations": c["variations"],
            "photo": [k for k, on in (("posting", c["photo_posting"]), ("contract", c["photo_contract"])) if on],
            "expected_flags": [{"level": level, "item": item} for level, item in c["expected"]],
        }
    (OUT / "answer_key.json").write_text(json.dumps(answer_key, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(CASES)}쌍 생성 → {OUT}")


if __name__ == "__main__":
    main()
