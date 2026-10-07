"use client";

import Link from "next/link";
import { useState } from "react";
import ConditionCard from "@/components/ConditionCard";
import { ApiError, extractPosting, type Posting } from "@/lib/api";
import { checkFile, FILE_ACCEPT, FILE_HINT } from "@/lib/upload";

type State =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "done"; posting: Posting };

function errorMessage(e: unknown): string {
  if (e instanceof ApiError) {
    if (e.status === 502) return "AI가 공고를 읽지 못했어요. 잠시 뒤 다시 시도해 주세요.";
    return e.detail;
  }
  // fetch 자체가 실패 = 서버가 꺼져 있거나 주소가 틀림
  return "서버에 연결할 수 없어요. 백엔드가 켜져 있는지 확인해 주세요.";
}

export default function PostingUpload() {
  const [file, setFile] = useState<File | null>(null);
  const [sourceUrl, setSourceUrl] = useState("");
  const [state, setState] = useState<State>({ kind: "idle" });

  const loading = state.kind === "loading";

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault(); // 브라우저 기본 동작(페이지 새로고침) 막기
    if (!file) return;

    const invalid = checkFile(file);
    if (invalid) {
      setState({ kind: "error", message: invalid });
      return;
    }

    setState({ kind: "loading" });
    try {
      const posting = await extractPosting(file, sourceUrl.trim() || undefined);
      setState({ kind: "done", posting });
    } catch (err) {
      setState({ kind: "error", message: errorMessage(err) });
    }
  }

  if (state.kind === "done") {
    const { posting } = state;
    return (
      <div className="space-y-4">
        <p className="rounded-lg bg-ok-soft px-4 py-3 text-ok">
          공고를 저장했어요. 읽은 내용이 맞는지 확인해 주세요.
        </p>
        <ConditionCard doc={posting.extracted_json} />
        <div className="flex flex-wrap gap-2">
          <Link
            href={`/postings/${posting.id}`}
            className="rounded-lg bg-primary px-5 py-3 font-bold text-white hover:bg-primary-dark"
          >
            다음: 계약서 올리기
          </Link>
          <button
            type="button"
            onClick={() => {
              setFile(null);
              setState({ kind: "idle" });
            }}
            className="rounded-lg border border-line bg-white px-5 py-3 hover:border-primary"
          >
            다른 공고 올리기
          </button>
        </div>
      </div>
    );
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-5 rounded-xl border border-line bg-white p-5"
      aria-busy={loading}
    >
      <div className="space-y-2">
        <label htmlFor="posting-file" className="block font-bold">
          공고 캡처 <span className="text-danger">*</span>
        </label>
        <input
          id="posting-file"
          type="file"
          accept={FILE_ACCEPT}
          disabled={loading}
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          className="block w-full text-sm file:mr-3 file:rounded-lg file:border-0 file:bg-primary-soft file:px-4 file:py-2 file:text-primary"
        />
        <p className="text-xs text-sub">{FILE_HINT}</p>
      </div>

      <div className="space-y-2">
        <label htmlFor="source-url" className="block font-bold">
          공고 링크 <span className="text-sm font-normal text-sub">(선택)</span>
        </label>
        <input
          id="source-url"
          type="url"
          value={sourceUrl}
          disabled={loading}
          onChange={(e) => setSourceUrl(e.target.value)}
          placeholder="https://"
          className="w-full rounded-lg border border-line px-3 py-2"
        />
        <p className="text-xs text-sub">기록용으로만 저장하고 접속하지는 않아요.</p>
      </div>

      {state.kind === "error" && (
        <p role="alert" className="rounded-lg bg-danger-soft px-4 py-3 text-danger">
          {state.message}
        </p>
      )}

      {loading && (
        <p role="status" className="rounded-lg bg-primary-soft px-4 py-3 text-primary">
          공고를 읽고 있어요. 1~2분 걸릴 수 있으니 창을 닫지 말아 주세요.
        </p>
      )}

      <button
        type="submit"
        disabled={!file || loading}
        className="w-full rounded-lg bg-primary px-5 py-3 font-bold text-white hover:bg-primary-dark disabled:cursor-not-allowed disabled:bg-line disabled:text-sub"
      >
        {loading ? "읽는 중…" : "공고 저장하기"}
      </button>
    </form>
  );
}
