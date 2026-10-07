import type { Level } from "@/lib/api";

// 등급별 색: 글자는 진한 색, 배경은 같은 계열의 옅은 색(-soft)
const STYLES: Record<Level, string> = {
  "불리 변경": "bg-danger-soft text-danger border-danger",
  "법 기준 확인": "bg-warn-soft text-warn border-warn",
  "누락": "bg-caution-soft text-caution border-caution",
  "모호": "bg-bg text-sub border-line",
  "동일·유리": "bg-ok-soft text-ok border-ok",
};

type Props = { level: Level };

export default function FindingBadge({ level }: Props) {
  return (
    <span
      className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-bold whitespace-nowrap ${STYLES[level]}`}
    >
      {level}
    </span>
  );
}
