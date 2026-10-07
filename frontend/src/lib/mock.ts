// 화면 개발용 가짜 데이터. 실제 API를 붙이면(8-4 5~7번) 쓰지 않는다.
import type { ConditionDoc, ExtractedField } from "./api";

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
