// 화면 개발용 가짜 데이터. 실제 API를 붙이면(8-4 5~7번) 쓰지 않는다.
import type { ConditionDoc, ExtractedField, Finding } from "./api";

function f(value: unknown = null, quote: string | null = null): ExtractedField {
  return { value, quote, verification: null };
}

// samples/case1_posting.json 과 같은 내용
export const MOCK_POSTING: ConditionDoc = {
  doc_type: f("공고"),
  company: f("(주)가나정밀(모의)", "(주)가나정밀(모의)"),
  headcount: f(),
  employment_type: f("정규직", "정규직"),
  contract_period_months: f(),
  probation: f(),
  workplace: f("경기 화성시", "경기 화성시 ○○로"),
  job_duties: f("생산관리 사무보조, 서류 정리", "생산관리 사무보조, 서류 정리"),
  work_days_per_week: f(5, "주 5일 (월~금)"),
  work_days_desc: f("월~금", "주 5일 (월~금)"),
  start_time: f("09:00", "09:00 ~ 18:00 (휴게 1시간)"),
  end_time: f("18:00", "09:00 ~ 18:00 (휴게 1시간)"),
  break_minutes: f(60, "휴게 1시간"),
  weekly_hours: f(),
  wage: f({ type: "월급", amount_min: 2500000, amount_max: 2500000 }, "월급 250만원"),
  comprehensive_wage: f(),
  allowances: f(),
  pay_day: f(),
  holidays: f(),
  annual_leave: f(),
  social_insurance: f("4대보험", "4대보험, 중식 제공"),
  penalty_or_damages_clause: f(),
};

// case1 공고 ↔ 계약서를 백엔드 규칙 엔진(compare)에 넣어 나온 실제 결과
export const MOCK_FINDINGS: Finding[] = [
  {
    level: "불리 변경",
    item: "고용형태",
    message: "공고 '정규직' → 계약서 '기타'",
    posting_quote: "정규직",
    contract_quote: "수습 종료 후 평가를 거쳐 정규직으로 전환한다.",
    basis: "",
  },
  {
    level: "불리 변경",
    item: "수습",
    message: "공고에 없던 수습 기간이 계약서에 있음",
    posting_quote: null,
    contract_quote: "입사일로부터 3개월은 수습기간으로 하며 수습기간 중 급여는 90%를 지급하고",
    basis: "",
  },
  {
    level: "법 기준 확인",
    item: "수습 감액",
    message: "수습 급여 90% — 감액은 1년 이상 계약·수습 3개월 이내·단순노무 제외일 때만 가능",
    posting_quote: null,
    contract_quote: "입사일로부터 3개월은 수습기간으로 하며 수습기간 중 급여는 90%를 지급하고",
    basis: "최저임금법 제5조②, 같은 법 시행령 제3조",
  },
  {
    level: "불리 변경",
    item: "근무일",
    message: "주 5일 → 주 5.5일",
    posting_quote: "주 5일 (월~금)",
    contract_quote: "매주 월~금 및 격주 토요일(09:00~13:00) 근무",
    basis: "",
  },
  {
    level: "불리 변경",
    item: "근로시간",
    message: "주 40.0시간 → 주 42.0시간",
    posting_quote: "09:00 ~ 18:00 (휴게 1시간)",
    contract_quote: "매주 월~금 및 격주 토요일(09:00~13:00) 근무",
    basis: "",
  },
  {
    level: "불리 변경",
    item: "포괄임금",
    message: "공고에 없던 포괄임금 (연장 20시간 포함) 신설",
    posting_quote: null,
    contract_quote: "월 20시간분 연장근로수당 포함 포괄 산정",
    basis: "",
  },
  {
    level: "불리 변경",
    item: "임금(기본 시급)",
    message: "연장수당 분리 후 기본 시급 11,987원 → 10,480원",
    posting_quote: "월급 250만원",
    contract_quote: "월 20시간분 연장근로수당 포함 포괄 산정",
    basis: "",
  },
  {
    level: "누락",
    item: "연차유급휴가",
    message: "계약서에 기재 없음 (상시 5인 이상 사업장인 경우)",
    posting_quote: null,
    contract_quote: null,
    basis: "근로기준법 제17조·제60조",
  },
];
