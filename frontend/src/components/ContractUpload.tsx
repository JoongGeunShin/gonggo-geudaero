"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ApiError, compareContract } from "@/lib/api";
import { checkFile, FILE_ACCEPT, FILE_HINT } from "@/lib/upload";

type State =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "done" }; // 결과 페이지로 이동하는 중

function errorMessage(e: unknown): string {
  if (e instanceof ApiError) {
    if (e.status === 502) return "AI가 계약서를 읽지 못했어요. 잠시 뒤 다시 시도해 주세요.";
    if (e.status === 409) return "이 공고는 읽은 조건이 없어 비교할 수 없어요. 공고를 다시 올려 주세요.";
    return e.detail;
  }
  return "서버에 연결할 수 없어요. 백엔드가 켜져 있는지 확인해 주세요.";
}

// 기다린 시간에 따라 안내 문구를 바꾼다 (AI 추출은 1~2분까지 걸릴 수 있음)
function waitingMessage(seconds: number): string {
  if (seconds < 10) return "계약서를 올리고 있어요.";
  if (seconds < 60) return "AI가 계약서 항목을 하나씩 읽고 있어요. 보통 1~2분 걸려요.";
  return "조금 오래 걸리고 있어요. 창을 닫지 말고 조금만 더 기다려 주세요.";
}

type Props = { postingId: number };

export default function ContractUpload({ postingId }: Props) {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [state, setState] = useState<State>({ kind: "idle" });
  const [elapsed, setElapsed] = useState(0);

  const loading = state.kind === "loading";
  const busy = loading || state.kind === "done";

  // 로딩 중에만 1초마다 경과 시간을 올린다. 로딩이 끝나면 타이머 정리
  useEffect(() => {
    if (!loading) return;
    const timer = setInterval(() => setElapsed((s) => s + 1), 1000);
    return () => clearInterval(timer);
  }, [loading]);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!file) return;

    const invalid = checkFile(file);
    if (invalid) {
      setState({ kind: "error", message: invalid });
      return;
    }

    setElapsed(0);
    setState({ kind: "loading" });
    try {
      const comparison = await compareContract(postingId, file);
      setState({ kind: "done" });
      router.push(`/comparisons/${comparison.id}`);
    } catch (err) {
      setState({ kind: "error", message: errorMessage(err) });
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-5 rounded-xl border border-line bg-white p-5"
      aria-busy={busy}
    >
      <div className="space-y-2">
        <label htmlFor="contract-file" className="block font-bold">
          근로계약서 사진 <span className="text-danger">*</span>
        </label>
        <input
          id="contract-file"
          type="file"
          accept={FILE_ACCEPT}
          disabled={busy}
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="block w-full text-sm file:mr-3 file:rounded-lg file:border-0 file:bg-primary-soft file:px-4 file:py-2 file:text-primary"
        />
        <p className="text-xs text-sub">{FILE_HINT}</p>
      </div>

      {state.kind === "error" && (
        <p role="alert" className="rounded-lg bg-danger-soft px-4 py-3 text-danger">
          {state.message}
        </p>
      )}

      {loading && (
        <p role="status" className="rounded-lg bg-primary-soft px-4 py-3 text-primary">
          {waitingMessage(elapsed)}{" "}
          <span className="text-sm tabular-nums">({elapsed}초)</span>
        </p>
      )}

      {state.kind === "done" && (
        <p role="status" className="rounded-lg bg-ok-soft px-4 py-3 text-ok">
          비교를 마쳤어요. 결과 화면으로 이동할게요.
        </p>
      )}

      <button
        type="submit"
        disabled={!file || busy}
        className="w-full rounded-lg bg-primary px-5 py-3 font-bold text-white hover:bg-primary-dark disabled:cursor-not-allowed disabled:bg-line disabled:text-sub"
      >
        {loading ? "비교하는 중…" : "공고와 비교하기"}
      </button>
    </form>
  );
}
