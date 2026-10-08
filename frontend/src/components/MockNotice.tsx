// 백엔드가 AI_PROVIDER=mock으로 추출한 결과임을 알리는 테스트용 표시
export function isMock(extractedBy: string | null | undefined): boolean {
  return extractedBy === "mock";
}

type Props = { docs: string[] }; // MOCK으로 추출된 문서 이름들 (예: ["공고", "계약서"])

export default function MockNotice({ docs }: Props) {
  if (docs.length === 0) return null;
  return (
    <p
      role="status"
      className="rounded-lg border border-warn bg-warn-soft px-4 py-3 text-sm text-warn"
    >
      <strong className="mr-2 rounded bg-warn px-1.5 py-0.5 text-xs text-white">MOCK 데이터</strong>
      {docs.join("·")} 내용은 AI가 이미지를 읽은 결과가 아니라 미리 준비한 샘플 정답이에요. 올린
      이미지와 다를 수 있어요.
    </p>
  );
}
