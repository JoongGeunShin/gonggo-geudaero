import { notFound } from "next/navigation";
import ConditionCard from "@/components/ConditionCard";
import ContractRequest from "@/components/ContractRequest";
import ContractUpload from "@/components/ContractUpload";
import StepIndicator from "@/components/StepIndicator";
import { ApiError, getPosting, type Posting } from "@/lib/api";

// 교부 요청 문구에 넣을 회사 이름: 사용자가 입력한 값 → 추출한 값 순서
function companyName(posting: Posting): string | null {
  const extracted = posting.extracted_json.company.value;
  return posting.company_name || (typeof extracted === "string" ? extracted : null);
}

// 서버 컴포넌트: 브라우저가 아니라 Next 서버에서 실행되어 공고를 미리 불러온다
export default async function PostingPage({ params }: PageProps<"/postings/[id]">) {
  const { id } = await params; // Next 15+ 에서 params는 Promise
  const postingId = Number(id);
  if (!Number.isInteger(postingId) || postingId <= 0) notFound(); // /postings/abc 같은 주소

  let posting: Posting;
  try {
    posting = await getPosting(postingId);
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) notFound();
    return (
      <p role="alert" className="rounded-lg bg-danger-soft px-4 py-3 text-danger">
        공고를 불러오지 못했어요. 백엔드가 켜져 있는지 확인해 주세요.
      </p>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <StepIndicator current={2} />
      <div>
        <h1 className="text-2xl font-bold">받은 근로계약서를 올려 주세요</h1>
        <p className="mt-2 text-sub">
          저장한 공고와 계약서를 항목별로 비교해서, 달라진 조건을 찾아 드려요.
        </p>
      </div>
      <ContractUpload postingId={posting.id} />
      <ContractRequest company={companyName(posting)} />
      <details>
        <summary className="cursor-pointer text-sm text-sub hover:text-primary">
          저장한 공고 조건 다시 보기
        </summary>
        <div className="mt-3">
          <ConditionCard doc={posting.extracted_json} />
        </div>
      </details>
    </div>
  );
}
