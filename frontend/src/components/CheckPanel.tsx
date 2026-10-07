import FindingBadge from "@/components/FindingBadge";
import type { Finding } from "@/lib/api";

type Props = { findings: Finding[] };

// ③ 서명 전 확인. 지금은 판정 결과로 확인할 항목만 보여준다
// (사업주에게 물어볼 질문 문장은 Phase 9 설명 생성에서 이 패널에 붙인다)
export default function CheckPanel({ findings }: Props) {
  const toCheck = findings.filter((f) => f.level !== "동일·유리");

  return (
    <section className="rounded-xl border border-line bg-white p-4">
      <h2 className="font-bold">서명 전에 확인할 항목</h2>
      {toCheck.length === 0 ? (
        <p className="mt-3 text-sm text-ok">
          공고와 다르거나 빠진 조건을 찾지 못했어요.
        </p>
      ) : (
        <ol className="mt-3 space-y-3 text-sm">
          {toCheck.map((f, i) => (
            <li key={`${f.item}-${i}`} className="flex gap-2">
              <span className="text-sub tabular-nums">{i + 1}.</span>
              <div className="space-y-1">
                <p>
                  <span className="font-bold">{f.item}</span>{" "}
                  <FindingBadge level={f.level} />
                </p>
                <p className="text-sub">{f.message}</p>
              </div>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
