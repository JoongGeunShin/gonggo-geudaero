import type { ConditionDoc, ExtractedField } from "@/lib/api";

type Row = { label: string; text: string | null; field: ExtractedField };

// ---------- 값 → 화면 글자 ----------

const won = (n: number) => `${n.toLocaleString("ko-KR")}원`;

function formatWage(v: unknown): string | null {
  const w = v as { type?: string; amount_min?: number; amount_max?: number } | null;
  if (!w || w.amount_min == null) return null;
  const amount =
    w.amount_max != null && w.amount_max !== w.amount_min
      ? `${won(w.amount_min)} ~ ${won(w.amount_max)}`
      : won(w.amount_min);
  return w.type ? `${w.type} ${amount}` : amount;
}

function formatProbation(v: unknown): string | null {
  const p = v as { exists?: boolean; months?: number; pay_rate_percent?: number } | null;
  if (!p) return null;
  if (!p.exists) return "없음";
  const parts = [p.months != null ? `${p.months}개월` : "있음"];
  if (p.pay_rate_percent != null) parts.push(`급여 ${p.pay_rate_percent}%`);
  return parts.join(", ");
}

function formatComprehensive(v: unknown): string | null {
  const c = v as { included?: boolean; overtime_hours_per_month?: number } | null;
  if (!c) return null;
  if (!c.included) return "없음";
  return c.overtime_hours_per_month != null
    ? `포함 (월 연장 ${c.overtime_hours_per_month}시간)`
    : "포함";
}

// 숫자·문자 값에 단위를 붙인다. 값이 없으면 null
function plain(v: unknown, unit = "", prefix = ""): string | null {
  if (v == null || v === "") return null;
  if (typeof v === "object") return JSON.stringify(v);
  return `${prefix}${v}${unit}`;
}

function buildRows(doc: ConditionDoc): Row[] {
  const { start_time: s, end_time: e } = doc;
  const hours = s.value && e.value ? `${s.value} ~ ${e.value}` : null;

  return [
    { label: "고용형태", text: plain(doc.employment_type.value), field: doc.employment_type },
    { label: "계약기간", text: plain(doc.contract_period_months.value, "개월"), field: doc.contract_period_months },
    { label: "수습", text: formatProbation(doc.probation.value), field: doc.probation },
    { label: "근무지", text: plain(doc.workplace.value), field: doc.workplace },
    { label: "업무", text: plain(doc.job_duties.value), field: doc.job_duties },
    { label: "근무일", text: plain(doc.work_days_per_week.value, "일", "주 "), field: doc.work_days_per_week },
    { label: "근무시간", text: hours, field: s },
    { label: "휴게시간", text: plain(doc.break_minutes.value, "분"), field: doc.break_minutes },
    { label: "주 근로시간", text: plain(doc.weekly_hours.value, "시간", "주 "), field: doc.weekly_hours },
    { label: "임금", text: formatWage(doc.wage.value), field: doc.wage },
    { label: "포괄임금", text: formatComprehensive(doc.comprehensive_wage.value), field: doc.comprehensive_wage },
    { label: "수당·상여", text: plain(doc.allowances.value), field: doc.allowances },
    { label: "임금 지급일", text: plain(doc.pay_day.value), field: doc.pay_day },
    { label: "휴일", text: plain(doc.holidays.value), field: doc.holidays },
    { label: "연차휴가", text: plain(doc.annual_leave.value), field: doc.annual_leave },
    { label: "4대보험", text: plain(doc.social_insurance.value), field: doc.social_insurance },
    { label: "위약금·배상", text: plain(doc.penalty_or_damages_clause.value), field: doc.penalty_or_damages_clause },
  ];
}

// ---------- 컴포넌트 ----------

type Props = { doc: ConditionDoc; title?: string };

export default function ConditionCard({ doc, title = "공고에서 읽은 조건" }: Props) {
  const rows = buildRows(doc);
  const company = plain(doc.company.value);

  return (
    <section className="rounded-xl border border-line bg-white">
      <header className="border-b border-line px-5 py-4">
        <h2 className="text-lg font-bold">{title}</h2>
        {company && <p className="mt-1 text-sm text-sub">{company}</p>}
      </header>
      <dl className="divide-y divide-line">
        {rows.map(({ label, text, field }) => (
          <div key={label} className="grid grid-cols-[7rem_1fr] gap-3 px-5 py-3">
            <dt className="text-sm text-sub">{label}</dt>
            <dd>
              {text ? (
                <span className="font-medium">{text}</span>
              ) : field.verification ? (
                <span className="text-caution">원문에서 확인 안 됨</span>
              ) : (
                <span className="text-sub">적혀 있지 않음</span>
              )}
              {text && field.quote && (
                <p className="mt-1 text-xs text-sub">“{field.quote}”</p>
              )}
            </dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
