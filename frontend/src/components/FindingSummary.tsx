import { LEVEL_STYLES } from "@/components/FindingBadge";
import { LEVELS, type Finding } from "@/lib/api";

type Props = { findings: Finding[] };

// 등급별 개수 카드. 0개인 등급은 회색으로 눌러서 눈에 덜 띄게
export default function FindingSummary({ findings }: Props) {
  return (
    <ul className="grid grid-cols-5 gap-1.5 sm:gap-2">
      {LEVELS.map((level) => {
        const count = findings.filter((f) => f.level === level).length;
        return (
          <li
            key={level}
            className={`rounded-lg border px-2 py-2 sm:px-3 ${
              count > 0 ? LEVEL_STYLES[level] : "border-line bg-white text-sub"
            }`}
          >
            <p className="text-xl font-bold tabular-nums sm:text-2xl">{count}</p>
            <p className="text-[11px] leading-tight sm:text-xs">{level}</p>
          </li>
        );
      })}
    </ul>
  );
}
