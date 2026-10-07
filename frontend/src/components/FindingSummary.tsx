import { LEVEL_STYLES } from "@/components/FindingBadge";
import { LEVELS, type Finding } from "@/lib/api";

type Props = { findings: Finding[] };

// 등급별 개수 카드. 0개인 등급은 회색으로 눌러서 눈에 덜 띄게
export default function FindingSummary({ findings }: Props) {
  return (
    <ul className="grid grid-cols-3 gap-2 sm:grid-cols-5">
      {LEVELS.map((level) => {
        const count = findings.filter((f) => f.level === level).length;
        return (
          <li
            key={level}
            className={`rounded-lg border px-3 py-2 ${
              count > 0 ? LEVEL_STYLES[level] : "border-line bg-white text-sub"
            }`}
          >
            <p className="text-2xl font-bold tabular-nums">{count}</p>
            <p className="text-xs">{level}</p>
          </li>
        );
      })}
    </ul>
  );
}
