"use client";

import { useRef, useState } from "react";
import { getLawArticle, type LawArticle } from "@/lib/api";
import { basisKeys, formatEffectiveDate } from "@/lib/law";

type View =
  | { kind: "loading"; key: string }
  | { kind: "error"; key: string }
  | { kind: "done"; article: LawArticle };

type Props = { basis: string };

// 판정 근거 + 조문 원문 보기 버튼. 누르면 GET /laws/{key} 로 받아 모달(<dialog>)에 띄운다
export default function LawBasis({ basis }: Props) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [view, setView] = useState<View | null>(null);
  const keys = basisKeys(basis);

  async function open(key: string) {
    setView({ kind: "loading", key });
    dialogRef.current?.showModal(); // 브라우저 기본 모달: 뒤 화면 막기, Esc로 닫기가 저절로 된다
    try {
      setView({ kind: "done", article: await getLawArticle(key) });
    } catch {
      setView({ kind: "error", key });
    }
  }

  return (
    <div className="mt-1 text-xs text-sub">
      <p>근거: {basis}</p>
      {keys.length > 0 && (
        <ul className="mt-1 flex flex-wrap gap-1">
          {keys.map((key) => (
            <li key={key}>
              <button
                type="button"
                onClick={() => open(key)}
                className="rounded border border-line bg-white px-1.5 py-0.5 text-primary hover:border-primary"
              >
                {key} 원문
              </button>
            </li>
          ))}
        </ul>
      )}

      <dialog
        ref={dialogRef}
        onClose={() => setView(null)}
        className="m-auto w-[min(40rem,calc(100%-2rem))] rounded-xl p-0 text-text backdrop:bg-black/40"
      >
        <div className="flex items-start justify-between gap-4 border-b border-line px-5 py-4">
          <h3 className="font-bold">
            {view?.kind === "done"
              ? `${view.article.law} ${view.article.article}(${view.article.title})`
              : view?.key}
          </h3>
          <form method="dialog">
            {/* method="dialog" 폼의 버튼은 누르면 dialog를 닫는다 */}
            <button className="text-sub hover:text-text" aria-label="닫기">
              ✕
            </button>
          </form>
        </div>
        <div className="max-h-[60vh] overflow-y-auto px-5 py-4 text-sm leading-relaxed">
          {view?.kind === "loading" && <p className="text-sub">조문을 불러오는 중…</p>}
          {view?.kind === "error" && (
            <p className="text-danger">조문을 불러오지 못했어요. 국가법령정보센터에서 확인해 주세요.</p>
          )}
          {view?.kind === "done" && (
            <>
              <p className="whitespace-pre-line">{view.article.text}</p>
              <p className="mt-4 text-xs text-sub">
                시행일 {formatEffectiveDate(view.article.effective_date)} · 출처 국가법령정보센터
              </p>
            </>
          )}
        </div>
      </dialog>
    </div>
  );
}
