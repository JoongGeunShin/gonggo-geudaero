"use client";

import { useState } from "react";

type Props = { text: string; label?: string };

// 클립보드 복사 버튼. 복사되면 2초 동안 "복사했어요"로 바뀐다
export default function CopyButton({ text, label = "복사하기" }: Props) {
  const [state, setState] = useState<"idle" | "done" | "error">("idle");

  async function copy() {
    try {
      await navigator.clipboard.writeText(text); // https 또는 localhost에서만 동작
      setState("done");
    } catch {
      setState("error");
    }
    setTimeout(() => setState("idle"), 2000);
  }

  return (
    <button
      type="button"
      onClick={copy}
      className="rounded-lg bg-primary px-3 py-1.5 text-sm font-bold text-white hover:bg-primary-dark"
    >
      {state === "done" ? "복사했어요" : state === "error" ? "복사 실패 — 직접 선택해 주세요" : label}
    </button>
  );
}
