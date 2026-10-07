import CopyButton from "@/components/CopyButton";
import FindingBadge from "@/components/FindingBadge";
import type { Explanation, Finding } from "@/lib/api";

type Props = { findings: Finding[]; explanation: Explanation | null };

// 사업주에게 그대로 보낼 수 있게 질문들을 번호 매겨 한 덩어리로
function questionsText(questions: string[]): string {
  return [
    "안녕하세요. 근로계약서 내용 중 채용공고와 다른 부분이 있어 몇 가지 여쭙습니다.",
    "",
    ...questions.map((q, i) => `${i + 1}. ${q}`),
    "",
    "확인 부탁드립니다. 감사합니다.",
  ].join("\n");
}

// ③ 서명 전 확인: 판정 결과마다 쉬운 말 설명 + 사업주에게 물어볼 질문, 질문 전체 복사
export default function CheckPanel({ findings, explanation }: Props) {
  const toCheck = findings.filter((f) => f.level !== "동일·유리");
  const byItem = new Map(explanation?.items.map((e) => [e.item, e]));
  const questions = toCheck.flatMap((f) => byItem.get(f.item)?.question ?? []);

  return (
    <section className="rounded-xl border border-line bg-white p-4">
      <h2 className="font-bold">서명 전에 확인할 항목</h2>
      {toCheck.length === 0 ? (
        <p className="mt-3 text-sm text-ok">
          공고와 다르거나 빠진 조건을 찾지 못했어요.
        </p>
      ) : (
        <>
          <ol className="mt-3 space-y-4 text-sm">
            {toCheck.map((f, i) => {
              const e = byItem.get(f.item);
              return (
                <li key={`${f.item}-${i}`} className="flex gap-2">
                  <span className="text-sub tabular-nums">{i + 1}.</span>
                  <div className="min-w-0 space-y-1">
                    <p>
                      <span className="font-bold">{f.item}</span>{" "}
                      <FindingBadge level={f.level} />
                    </p>
                    <p className="text-sub">{e?.summary ?? f.message}</p>
                    {e && (
                      <p className="rounded-lg bg-primary-soft px-3 py-2 leading-relaxed">
                        <span className="mr-1 text-xs font-bold text-primary">질문</span>
                        {e.question}
                      </p>
                    )}
                  </div>
                </li>
              );
            })}
          </ol>
          {questions.length > 0 && (
            <div className="mt-4 space-y-2 border-t border-line pt-4">
              <p className="text-xs text-sub">
                질문을 복사해서 문자나 메일로 사업주에게 보낼 수 있어요.
              </p>
              <CopyButton text={questionsText(questions)} label="질문 복사하기" />
            </div>
          )}
        </>
      )}
    </section>
  );
}
