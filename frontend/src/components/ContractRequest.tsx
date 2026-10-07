import CopyButton from "@/components/CopyButton";
import LawBasis from "@/components/LawBasis";
import { contractRequestText } from "@/lib/templates";

type Props = { company?: string | null };

// 계약서를 아직 못 받았을 때: 사업주에게 보낼 교부 요청 문구 + 복사 버튼
export default function ContractRequest({ company }: Props) {
  const text = contractRequestText(company);

  return (
    <details className="rounded-xl border border-line bg-white p-4">
      <summary className="cursor-pointer font-bold">아직 근로계약서를 받지 못했나요?</summary>
      <div className="mt-3 space-y-3 text-sm">
        <p className="text-sub">
          일을 시작하기 전에 계약서를 받아 두면 공고와 비교해 볼 수 있어요. 아래 문구를 복사해서 문자나
          메일로 보내 보세요.
        </p>
        <p className="whitespace-pre-line rounded-lg bg-bg p-3 leading-relaxed">{text}</p>
        <div className="flex flex-wrap items-start justify-between gap-2">
          <LawBasis basis="근로기준법 제17조" />
          <CopyButton text={text} label="문구 복사하기" />
        </div>
      </div>
    </details>
  );
}
