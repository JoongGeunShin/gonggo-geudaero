import csv
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parents[2] / "data" / "min_wage.csv"


def load_min_wage(path: Path = CSV_PATH) -> dict[int, int]:
    """연도별 최저 시간급 표를 {연도: 시간급}으로 돌려준다."""
    with path.open(encoding="utf-8", newline="") as f:
        return {int(row["연도"]): int(row["시간급"]) for row in csv.DictReader(f)}
