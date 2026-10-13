"use client";

import { FILE_ACCEPT, FILE_HINT } from "@/lib/upload";
import { useCallback, useState } from "react";

type Props = {
  id: string;
  file: File | null;
  onFileChange: (file: File | null) => void;
  disabled?: boolean;
};

// 클릭해서 고르기 + 끌어다 놓기를 모두 지원하는 파일 선택 영역
// 파일 상태는 부모가 들고, 여기서는 "끌어오는 중인지"만 관리한다
export default function FileDropzone({
  id,
  file,
  onFileChange,
  disabled,
}: Props) {
  const [dragging, setDragging] = useState(false);

  function handleDragEnter(e: React.DragEvent<HTMLLabelElement>) {
    e.preventDefault();
    if (!disabled) setDragging(true);
  }

  function handleDragOver(e: React.DragEvent<HTMLLabelElement>) {
    // 이걸 막지 않으면 브라우저가 "여기는 놓을 수 없는 곳"으로 판단해 drop이 안 일어난다
    e.preventDefault();
  }

  function handleDragLeave(e: React.DragEvent<HTMLLabelElement>) {
    // 안쪽 글자 위로 옮겨갈 때도 dragleave가 발생하므로, 영역 밖으로 나간 경우만 처리
    if (e.currentTarget.contains(e.relatedTarget as Node | null)) return;
    setDragging(false);
  }

  function handleDrop(e: React.DragEvent<HTMLLabelElement>) {
    // 막지 않으면 브라우저가 파일을 새 탭으로 열어버린다
    e.preventDefault();
    setDragging(false);
    if (disabled) return;
    onFileChange(e.dataTransfer.files[0] ?? null);
  }

  return (
    <label
      htmlFor={id}
      onDragEnter={handleDragEnter}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={[
        "flex flex-col items-center justify-center gap-1 rounded-lg border-2 border-dashed px-4 py-8 text-center transition-colors focus-within:ring-2 focus-within:ring-primary",
        disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer",
        dragging
          ? "border-primary bg-primary-soft"
          : "border-line hover:border-primary",
      ].join(" ")}
    >
      <input
        id={id}
        type="file"
        accept={FILE_ACCEPT}
        disabled={disabled}
        onChange={(e) => {
          onFileChange(e.target.files?.[0] ?? null);
          // 같은 파일을 다시 골라도 onChange가 일어나도록 비워둔다 (선택된 파일은 부모 상태가 기억)
          e.target.value = "";
        }}
        className="sr-only"
      />
      {file ? (
        <>
          <FilePreview file={file} />
          <span className="font-bold text-primary">{file.name}</span>
        </>
      ) : (
        <span className="font-bold">
          {dragging ? "여기에 놓으세요" : "파일을 끌어오거나 눌러서 선택"}
        </span>
      )}
      <span className="text-xs text-sub">
        {file ? "다른 파일로 바꾸려면 다시 끌어오거나 누르세요" : FILE_HINT}
      </span>
    </label>
  );
}

// 고른 파일을 작게 미리 보여준다. 이미지는 썸네일, PDF는 표시만.
function FilePreview({ file }: { file: File }) {
  // img가 화면에 붙을 때 임시 주소를 만들고, 떨어지거나 파일이 바뀌면 해제한다
  // (React 19: ref 콜백이 돌려준 함수는 cleanup으로 실행된다)
  const attachPreview = useCallback(
    (img: HTMLImageElement | null) => {
      if (!img) return;
      // 서버에 올리지 않고 브라우저 메모리의 파일을 바로 보여주는 임시 주소(blob:...)
      const objectUrl = URL.createObjectURL(file);
      img.src = objectUrl;
      return () => URL.revokeObjectURL(objectUrl);
    },
    [file],
  );

  if (!file.type.startsWith("image/")) {
    return (
      <span className="rounded-md bg-primary-soft px-3 py-2 text-sm font-bold text-primary">
        PDF
      </span>
    );
  }
  return (
    // blob: 주소는 next/image 최적화 대상이 아니라서 일반 img를 쓴다
    // eslint-disable-next-line @next/next/no-img-element
    <img
      ref={attachPreview}
      alt="고른 파일 미리보기"
      className=" max-w-full rounded-md border border-line object-contain"
    />
  );
}
