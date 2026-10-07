import PostingUpload from "@/components/PostingUpload";
import StepIndicator from "@/components/StepIndicator";

export default function Home() {
  return (
    <div className="space-y-6">
      <StepIndicator current={1} />
      <div>
        <h1 className="text-2xl font-bold">지원한 공고를 저장하세요</h1>
        <p className="mt-2 text-sub">
          지원할 때 본 공고 화면을 캡처해서 올리면, 나중에 받은 계약서와 비교할 수 있어요.
        </p>
      </div>
      <PostingUpload />
    </div>
  );
}
