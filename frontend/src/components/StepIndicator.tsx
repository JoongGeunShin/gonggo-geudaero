const STEPS = ["공고 저장", "계약서 올리기", "결과 확인"] as const;
type Props = { current: 1 | 2 | 3 };

export default function StepIndicator({ current }: Props) {
  return (
    <ol className="flex items-center gap-2">
      {STEPS.map((label, i) => {
        const step = i + 1;
        const done = step < current;
        const active = step === current;
        return (
          <li
            key={label}
            className="flex items-center gap-2"
            aria-current={active ? "step" : undefined}
          >
            {i > 0 && <span className="h-px w-6 bg-line md:w-12" aria-hidden />}
            <span
              className={`flex h-7 w-7 items-center justify-center rounded-full text-sm font-bold ${
                active || done
                  ? "bg-primary text-white"
                  : "border border-line bg-white text-sub"
              }`}
            >
              {done ? "✓" : step}
            </span>
            {/* 모바일에서는 현재 단계 이름만 보여서 줄바꿈을 막는다 */}
            <span
              className={`whitespace-nowrap text-sm ${
                active ? "font-bold text-text" : "hidden text-sub sm:inline"
              }`}
            >
              {label}
            </span>
          </li>
        );
      })}
    </ol>
  );
}
