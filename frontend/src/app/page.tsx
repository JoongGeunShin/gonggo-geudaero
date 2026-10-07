import StepIndicator from "@/components/StepIndicator";
export default function Home() {
  return (
    <div className="space-y-6">
      <StepIndicator current={1} />
      <h1 className="text-2xl font-bold">지원한 공고를 저장하세요</h1>
      <p className="text-sub">업로드 화면은 5번 단계에서 붙입니다.</p>
    </div>
  );
}
