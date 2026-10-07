const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export type ExtractedField = {
  value: unknown;
  quote: string | null;
  verification: "quote_not_found" | "quote_missing" | null;
};

export type ConditionDoc = {
  doc_type: ExtractedField;
  company: ExtractedField;
  headcount: ExtractedField;
  employment_type: ExtractedField;
  contract_period_months: ExtractedField;
  probation: ExtractedField;
  workplace: ExtractedField;
  job_duties: ExtractedField;
  work_days_per_week: ExtractedField;
  work_days_desc: ExtractedField;
  start_time: ExtractedField;
  end_time: ExtractedField;
  break_minutes: ExtractedField;
  weekly_hours: ExtractedField;
  wage: ExtractedField;
  comprehensive_wage: ExtractedField;
  allowances: ExtractedField;
  pay_day: ExtractedField;
  holidays: ExtractedField;
  annual_leave: ExtractedField;
  social_insurance: ExtractedField;
  penalty_or_damages_clause: ExtractedField;
};

export type Level =
  | "불리 변경"
  | "법 기준 확인"
  | "누락"
  | "모호"
  | "동일·유리";

export type Finding = {
  level: Level;
  item: string;
  message: string;
  posting_quote: string | null;
  contract_quote: string | null;
  basis: string;
};

export type Posting = {
  id: number;
  created_at: string; // datetime은 JSON에서 ISO 문자열로 온다
  source_type: "capture" | "url" | "manual";
  source_url: string | null;
  raw_text: string | null;
  extracted_json: ConditionDoc;
  company_name: string | null;
  b_no: string | null;
  nts_status_json: Record<string, unknown> | null;
};

export type Comparison = {
  id: number;
  posting_id: number;
  document_id: number;
  findings_json: Finding[];
  explanation_json: Record<string, unknown> | null;
  created_at: string;
};

export type LawArticle = {
  law: string;
  article: string;
  title: string;
  effective_date: string;
  text: string;
};

// ---------- 에러 ----------

export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
  ) {
    super(`${status} ${detail}`);
  }
}

// ---------- 공통 요청 함수 ----------

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, init);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail =
        typeof body.detail === "string"
          ? body.detail
          : JSON.stringify(body.detail);
    } catch {}
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

// ---------- 엔드포인트 ----------

export function extractPosting(file: File, sourceUrl?: string) {
  const form = new FormData();
  form.append("file", file);
  if (sourceUrl) form.append("source_url", sourceUrl);
  return request<Posting>("/postings/extract", { method: "POST", body: form });
}

export function getPosting(id: number) {
  return request<Posting>(`/postings/${id}`);
}

export function checkBusiness(postingId: number, bNo: string) {
  return request<Posting>(`/postings/${postingId}/business-check`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ b_no: bNo }),
  });
}

export function compareContract(postingId: number, file: File) {
  const form = new FormData();
  form.append("file", file);
  return request<Comparison>(`/postings/${postingId}/compare`, {
    method: "POST",
    body: form,
  });
}

export function getComparison(id: number) {
  return request<Comparison>(`/comparisons/${id}`);
}

export function getLawArticle(key: string) {
  return request<LawArticle>(`/laws/${encodeURIComponent(key)}`);
}
