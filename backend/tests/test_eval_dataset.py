"""평가 데이터 무결성: eval/data의 정답 JSON 40쌍을 엔진에 넣으면 answer_key.json의 경고가 정확히 나와야 한다.

여기가 깨지면 데이터(정답)가 틀렸거나 엔진 규칙이 바뀐 것이다. 둘 중 무엇인지 확인하고 고칠 것.
"""

import json
from pathlib import Path

import pytest

from app.rules.engine import GREEN, compare
from app.schemas import ConditionDoc

DATA = Path(__file__).resolve().parents[2] / "eval" / "data"
ANSWER_KEY = json.loads((DATA / "answer_key.json").read_text(encoding="utf-8"))


def load(pair, kind):
    return ConditionDoc.model_validate_json((DATA / f"{pair}_{kind}.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("pair", sorted(ANSWER_KEY))
def test_gold_pair_matches_answer_key(pair):
    findings = compare(load(pair, "posting"), load(pair, "contract"))
    found = sorted((f.level, f.item) for f in findings if f.level != GREEN)
    expected = sorted((e["level"], e["item"]) for e in ANSWER_KEY[pair]["expected_flags"])
    assert found == expected


def test_dataset_has_40_pairs_with_images():
    assert len(ANSWER_KEY) == 40
    for pair in ANSWER_KEY:
        for kind in ("posting", "contract"):
            assert (DATA / f"{pair}_{kind}.png").exists()
            assert (DATA / f"{pair}_{kind}.txt").exists()
