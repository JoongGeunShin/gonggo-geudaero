import { notFound } from "next/navigation";
import CheckPanel from "@/components/CheckPanel";
import CompareTable from "@/components/CompareTable";
import ConditionCard from "@/components/ConditionCard";
import FindingSummary from "@/components/FindingSummary";
import StepIndicator from "@/components/StepIndicator";
import { ApiError, getComparison, getPosting, LEVELS, type Comparison, type Posting } from "@/lib/api";

// 백엔드(SQLite)는 시간대 없이 UTC로 준다 → 'Z'를 붙여 UTC로 읽고 한국 시간으로 표시
function formatSavedAt(iso: string): string {
  const utc = /(Z|[+-]\d{2}:?\d{2})$/.test(iso) ? iso : `${iso}Z`;
  return new Date(utc).toLocaleString("ko-KR", {
    timeZone: "Asia/Seoul",
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function businessStatus(posting: Posting): string | null {
  if (!posting.b_no) return null; // 조회를 안 했으면 표시하지 않음
  const stt = posting.nts_status_json?.b_stt;
  return typeof stt === "string" && stt ? stt : "확인 불가";
}

function ColumnTitle({ no, children }: { no: string; children: React.ReactNode }) {
  return (
    <h2 className="mb-3 text-sm font-bold text-primary">
      {no} {children}
    </h2>
  );
}

export default async function ComparisonPage({ params }: PageProps<"/comparisons/[id]">) {
  const { id } = await params;
  const comparisonId = Number(id);
  if (!Number.isInteger(comparisonId) || comparisonId <= 0) notFound();

  let comparison: Comparison;
  let posting: Posting;
  try {
    comparison = await getComparison(comparisonId);
    posting = await getPosting(comparison.posting_id); // 결과에 공고 id가 있어야 알 수 있어서 순서대로
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) notFound();
    return (
      <p role="alert" className="rounded-lg bg-danger-soft px-4 py-3 text-danger">
        결과를 불러오지 못했어요. 백엔드가 켜져 있는지 확인해 주세요.
      </p>
    );
  }

  // 심각한 등급이 위로 오게 (같은 등급끼리는 엔진이 준 순서 유지)
  const findings = [...comparison.findings_json].sort(
    (a, b) => LEVELS.indexOf(a.level) - LEVELS.indexOf(b.level),
  );
  const status = businessStatus(posting);

  return (
    <div className="space-y-6">
      <StepIndicator current={3} />

      <div className="grid gap-6 lg:grid-cols-[16rem_1fr_16rem]">
        <div>
          <ColumnTitle no="①">지원 시점 공고</ColumnTitle>
          <ConditionCard doc={posting.extracted_json} compact />
          <p className="mt-2 text-xs text-sub">저장 {formatSavedAt(posting.created_at)}</p>
          {status && <p className="text-xs text-sub">사업자 상태: {status}</p>}
        </div>

        <div className="min-w-0">
          <ColumnTitle no="②">공고 ↔ 계약서 항목별 대조</ColumnTitle>
          <div className="space-y-4">
            <FindingSummary findings={findings} />
            <CompareTable findings={findings} />
          </div>
        </div>

        <div>
          <ColumnTitle no="③">서명 전 확인</ColumnTitle>
          <CheckPanel findings={findings} />
        </div>
      </div>
    </div>
  );
}
