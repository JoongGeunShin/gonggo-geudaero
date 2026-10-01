"""통합 테스트: samples/의 공고·계약서 3쌍을 엔진에 넣고 answer_key.json과 비교한다."""

import json
from pathlib import Path

import pytest

from app.rules.engine import AMBER, RED, compare
from app.schemas import ConditionDoc

SAMPLES = Path(__file__).resolve().parents[2] / "samples"  # backend/tests → 저장소 루트/samples
ANSWER_KEY = json.loads((SAMPLES / "answer_key.json").read_text(encoding="utf-8"))


def load(case, kind):
    return ConditionDoc.model_validate_json((SAMPLES / f"{case}_{kind}.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", sorted(ANSWER_KEY))
def test_engine_matches_answer_key(case):
    findings = compare(load(case, "posting"), load(case, "contract"))
    found = {(f.level, f.item) for f in findings if f.level in (RED, AMBER)}
    expected = {(e["level"], e["item"]) for e in ANSWER_KEY[case]["expected_flags"]}

    assert expected - found == set(), "놓친 경고"
    assert found - expected == set(), "정답지에 없는 경고(오탐)"


def test_answer_key_has_12_flags():
    # 정답지 자체가 바뀌면 12/12 기준도 다시 확인해야 하므로 개수를 고정
    assert sum(len(c["expected_flags"]) for c in ANSWER_KEY.values()) == 12
