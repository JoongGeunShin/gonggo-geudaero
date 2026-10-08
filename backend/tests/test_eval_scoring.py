"""eval/run_eval.py의 채점 규칙과 mock 전체 실행 (정답을 돌려주므로 모든 지표가 100%여야 한다)."""

import importlib.util
import json
from pathlib import Path

import pytest

EVAL_DIR = Path(__file__).resolve().parents[2] / "eval"
spec = importlib.util.spec_from_file_location("run_eval", EVAL_DIR / "run_eval.py")
run_eval = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_eval)


@pytest.mark.parametrize("pred, gold", [
    (None, None),
    ({"exists": False, "months": None}, None),          # '없음'을 객체로 답해도 값 없음과 같다
    ({"included": False}, None),
    ("9:00", "09:00"),
    (2500000.0, 2500000),
    ({"type": "월급", "amount_min": 2500000, "amount_max": 2500000},
     {"type": "월급", "amount_min": 2500000, "amount_max": 2500000}),
])
def test_same_values(pred, gold):
    assert run_eval.same(pred, gold)


@pytest.mark.parametrize("pred, gold", [
    (None, 5),
    (5.5, 5),
    ({"exists": True, "months": 3, "pay_rate_percent": 90}, None),
    ({"type": "월급", "amount_min": 2300000}, {"type": "월급", "amount_min": 2500000}),
    (True, 1),
])
def test_different_values(pred, gold):
    assert not run_eval.same(pred, gold)


def test_text_fields_accept_more_detailed_value():
    assert run_eval.field_ok("workplace", "경기 화성시 ○○로 본사", "경기 화성시 ○○로")
    assert not run_eval.field_ok("workplace", "인천 남동구", "경기 시흥시")


def test_presence_fields_only_check_existence():
    assert run_eval.field_ok("holidays", "일요일", "매주 일요일")
    assert not run_eval.field_ok("annual_leave", None, "근로기준법에 따라 부여")


def test_mock_run_scores_everything(tmp_path):
    from app.ai.mock import MockExtractor

    answer_key = json.loads((run_eval.DATA / "answer_key.json").read_text(encoding="utf-8"))
    runner = run_eval.CachedRunner(MockExtractor(samples_dir=run_eval.DATA), tmp_path, use_cache=True, sleep=0)
    report = run_eval.evaluate(runner, answer_key, sorted(answer_key))
    s = run_eval.summarize(report)

    assert s["pairs_evaluated"] == 40
    assert s["field_accuracy"]["전체"]["rate"] == 1
    assert s["detection_core"] == {"hit": 50, "expected": 50, "recall": 1, "extra": 0}
    assert s["pairs_exact"] == 40
