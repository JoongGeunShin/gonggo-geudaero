import FindingBadge from "@/components/FindingBadge";
import LawBasis from "@/components/LawBasis";
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
    <>
      {/* 모바일: 표 대신 항목별 카드 (가로 스크롤 없이 세로로 읽기) */}
      <ul className="space-y-3 md:hidden">
        {findings.map((f, i) => (
          <li key={`${f.item}-${i}`} className="rounded-xl border border-line bg-white p-4 text-sm">
            <div className="flex items-start justify-between gap-2">
              <p className="font-bold">{f.item}</p>
              <FindingBadge level={f.level} />
            </div>
            <p className="mt-1">{f.message}</p>
            <dl className="mt-3 space-y-2 rounded-lg bg-bg p-3">
              <div>
                <dt className="text-xs text-sub">공고</dt>
                <dd><Quote text={f.posting_quote} empty="공고에 없음" /></dd>
              </div>
              <div>
                <dt className="text-xs text-sub">계약서 인용</dt>
                <dd><Quote text={f.contract_quote} empty="계약서에 없음" /></dd>
              </div>
            </dl>
            {f.basis && <LawBasis basis={f.basis} />}
          </li>
        ))}
      </ul>

      {/* md 이상: 표 */}
      <div className="hidden overflow-x-auto rounded-xl border border-line bg-white md:block">
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
                  {f.basis && <LawBasis basis={f.basis} />}
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
    </>
  );
}
