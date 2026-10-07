import FindingBadge from "@/components/FindingBadge";
import type { Finding } from "@/lib/api";

function Quote({ text, empty }: { text: string | null; empty: string }) {
  return text ? (
    <span>“{text}”</span>
  ) : (
    <span className="text-sub">{empty}</span>
  );
}

type Props = { findings: Finding[] };

export default function CompareTable({ findings }: Props) {
  return (
    <div className="overflow-x-auto rounded-xl border border-line bg-white">
      <table className="w-full min-w-[640px] text-left text-sm">
        <thead className="bg-primary-soft text-text">
          <tr>
            <th scope="col" className="w-1/4 px-4 py-3 font-bold">항목</th>
            <th scope="col" className="w-1/4 px-4 py-3 font-bold">공고</th>
            <th scope="col" className="w-1/3 px-4 py-3 font-bold">계약서 인용</th>
            <th scope="col" className="px-4 py-3 font-bold">판정</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {findings.map((f, i) => (
            <tr key={`${f.item}-${i}`} className="align-top">
              <th scope="row" className="px-4 py-3 font-normal">
                <p className="font-bold">{f.item}</p>
                <p className="mt-1 text-text">{f.message}</p>
                {f.basis && (
                  <p className="mt-1 text-xs text-sub">근거: {f.basis}</p>
                )}
              </th>
              <td className="px-4 py-3">
                <Quote text={f.posting_quote} empty="공고에 없음" />
              </td>
              <td className="px-4 py-3">
                <Quote text={f.contract_quote} empty="계약서에 없음" />
              </td>
              <td className="px-4 py-3">
                <FindingBadge level={f.level} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
