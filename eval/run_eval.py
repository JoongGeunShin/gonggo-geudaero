"""Phase 10 정확도 평가: 합성 40쌍을 추출 → 인용 검증·마스킹 → 판정하고 정답과 비교한다.

    backend/.venv/Scripts/python eval/run_eval.py --provider mock          # 파이프라인 점검 (정답을 그대로 돌려줌 → 100%)
    backend/.venv/Scripts/python eval/run_eval.py --provider gemini        # 실제 평가 (.env의 GEMINI_MODEL)
    backend/.venv/Scripts/python eval/run_eval.py --provider gemini --pairs pair01,pair07 --sleep 10

- 한 번 추출한 결과는 eval/cache/<제공자_모델_프롬프트>/에 저장하고, 다시 돌릴 때는 부르지 않는다 (--no-cache로 무시).
- 무료 티어 분당 한도 때문에 실제 호출 사이에 --sleep 초만큼 쉰다. 연속 3번 실패하면 한도 소진으로 보고 멈춘다.
- 결과는 표로 출력하고 eval/results/날짜_프롬프트버전_제공자.json에 저장한다.

합성 데이터 기준 숫자다. 실제 문서 정확도와 다를 수 있다.
"""

import argparse
import json
import sys
import time
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path

EVAL_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(EVAL_DIR.parent / "backend"))

from app.ai.base import ExtractionError, ExtractionResult  # noqa: E402
from app.ai.mask import mask_result  # noqa: E402
from app.ai.prompts import EXTRACT_PROMPT_VERSION  # noqa: E402
from app.ai.verify import normalize, verify_quotes  # noqa: E402
from app.rules.engine import AMBER, GRAY, GREEN, RED, YELLOW, compare  # noqa: E402
from app.schemas import ConditionDoc  # noqa: E402

DATA = EVAL_DIR / "data"
KINDS = ("posting", "contract")

# 판정에 쓰이는 항목만 정확도를 잰다 (test_kit/run_test.py와 같은 16개)
SCORED_EXACT = ["employment_type", "contract_period_months", "probation", "work_days_per_week",
                "start_time", "end_time", "break_minutes", "weekly_hours", "wage",
                "comprehensive_wage", "headcount"]
SCORED_TEXT = ["workplace", "pay_day"]                                    # 한쪽이 다른 쪽을 포함하면 정답
SCORED_PRESENCE = ["holidays", "annual_leave", "penalty_or_damages_clause"]  # 있다/없다만
SCORED = SCORED_EXACT + SCORED_TEXT + SCORED_PRESENCE

CORE = {RED, AMBER}        # 놓치면 안 되는 경고 (재현율의 기준)
MINOR = {YELLOW, GRAY}     # 누락·모호


# ---------------------------------------------------------------- 값 비교

def is_empty(v) -> bool:
    """값 없음으로 볼 것: null, 빈 문자열, {}, 그리고 '없음'을 뜻하는 {"exists": false}·{"included": false}."""
    if v in (None, "", {}):
        return True
    if isinstance(v, dict) and ("exists" in v or "included" in v):
        return not (v.get("exists") or v.get("included"))
    return False


def _norm_time(v):
    if isinstance(v, str) and ":" in v:
        h, m = v.strip().split(":")[:2]
        if h.isdigit() and m.isdigit():
            return f"{int(h):02d}:{int(m):02d}"
    return v


def same(a, b) -> bool:
    if is_empty(a) and is_empty(b):
        return True
    if is_empty(a) or is_empty(b):
        return False
    if isinstance(a, dict) and isinstance(b, dict):
        return all(same(a.get(k), b.get(k)) for k in set(a) | set(b))
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(a - b) < 1e-6
    return normalize(str(_norm_time(a))) == normalize(str(_norm_time(b)))


def field_ok(key, pred, gold) -> bool:
    if key in SCORED_PRESENCE:
        return is_empty(pred) == is_empty(gold)
    if key in SCORED_TEXT and not is_empty(pred) and not is_empty(gold):
        p, g = normalize(str(pred)), normalize(str(gold))
        return p in g or g in p   # 엔진의 근무지 비교와 같은 기준
    return same(pred, gold)


def field_rows(pred: ConditionDoc, gold: ConditionDoc) -> list[dict]:
    rows = []
    for key in SCORED:
        p, g = getattr(pred, key), getattr(gold, key)
        rows.append({"field": key, "ok": field_ok(key, p.value, g.value), "pred": p.value, "gold": g.value,
                     "dropped": p.verification})
    return rows


def text_ratio(pred_text: str, gold_text: str) -> float:
    """OCR 원문 일치율 (공백 무시, 0~1). 이미지에 그린 글자(.txt)와 비교한다."""
    return round(SequenceMatcher(None, normalize(pred_text), normalize(gold_text), autojunk=False).ratio(), 4)


def flags(findings) -> set[tuple[str, str]]:
    return {(f.level, f.item) for f in findings if f.level != GREEN}


# ---------------------------------------------------------------- 추출 (캐시)

def make_extractor(provider: str, model: str):
    if provider == "mock":
        from app.ai.mock import MockExtractor
        return MockExtractor(samples_dir=DATA), "mock"
    if provider == "gemini":
        from app.ai.gemini import GeminiExtractor
        from app.config import settings
        model = model or settings.gemini_model
        if not settings.gemini_api_key or not model:
            sys.exit("GEMINI_API_KEY와 GEMINI_MODEL(.env 또는 --model)이 필요합니다")
        return GeminiExtractor(api_key=settings.gemini_api_key, model=model), model
    sys.exit(f"지원하지 않는 제공자: {provider}")


class CachedRunner:
    """문서 한 장 추출. 캐시가 있으면 그대로 쓰고, 없으면 호출 후 저장한다. 실패는 저장하지 않는다(다음에 재시도)."""

    def __init__(self, extractor, cache_dir: Path, use_cache: bool, sleep: float):
        self.extractor, self.cache_dir, self.use_cache, self.sleep = extractor, cache_dir, use_cache, sleep
        self.called = self.cached = 0
        self._last_call = 0.0
        cache_dir.mkdir(parents=True, exist_ok=True)

    def extract(self, name: str, kind: str) -> tuple[ExtractionResult, float]:
        path = self.cache_dir / f"{name}.json"
        if self.use_cache and path.exists():
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.cached += 1
            return ExtractionResult.model_validate(saved["result"]), saved["seconds"]
        wait = self.sleep - (time.monotonic() - self._last_call)
        if self.called and wait > 0:
            time.sleep(wait)
        start = time.monotonic()
        try:
            result = self.extractor.extract((DATA / f"{name}.png").read_bytes(), "image/png", kind)
        finally:
            self._last_call = time.monotonic()
            self.called += 1
        seconds = round(time.monotonic() - start, 1)
        path.write_text(json.dumps({"seconds": seconds, "result": result.model_dump()}, ensure_ascii=False, indent=1),
                        encoding="utf-8")
        return result, seconds


# ---------------------------------------------------------------- 평가

def evaluate(runner: CachedRunner, answer_key: dict, pairs: list[str], max_consecutive_errors: int = 3) -> dict:
    report = {}
    errors_in_row = 0
    for pair in pairs:
        docs, row = {}, {"photo": answer_key[pair]["photo"], "variations": answer_key[pair]["variations"]}
        for kind in KINDS:
            name = f"{pair}_{kind}"
            try:
                raw, seconds = runner.extract(name, kind)
                errors_in_row = 0
            except ExtractionError as e:
                print(f"  ✗ {name}: 추출 실패 — {e}", flush=True)
                row["error"] = f"{kind}: {e}"
                errors_in_row += 1
                break
            # 서비스(services/extraction.py)와 같은 순서: 인용 검증 → 마스킹
            result = mask_result(verify_quotes(raw))
            gold = ConditionDoc.model_validate_json((DATA / f"{name}.json").read_text(encoding="utf-8"))
            gold_text = (DATA / f"{name}.txt").read_text(encoding="utf-8")
            docs[kind] = result.fields
            row[kind] = {"seconds": seconds, "ocr_ratio": text_ratio(raw.full_text, gold_text),
                         "fields": field_rows(result.fields, gold)}
        if "error" not in row:
            found = flags(compare(docs["posting"], docs["contract"]))
            expected = {(e["level"], e["item"]) for e in answer_key[pair]["expected_flags"]}
            row.update(expected=sorted(expected), found=sorted(found),
                       missed=sorted(expected - found), extra=sorted(found - expected))
            mark = "✓" if found == expected else "△"
            print(f"  {mark} {pair} {answer_key[pair]['desc']}"
                  + (f" | 놓침 {row['missed']}" if row["missed"] else "")
                  + (f" | 추가 {row['extra']}" if row["extra"] else ""), flush=True)
        report[pair] = row
        if errors_in_row >= max_consecutive_errors:
            print(f"  연속 {errors_in_row}번 실패 — 한도 소진으로 보고 멈춤. 나중에 다시 실행하면 캐시 이후부터 이어감.")
            break
    return report


def _pct(hit, total):
    return f"{hit}/{total} ({hit / total:.1%})" if total else "0/0"


def summarize(report: dict) -> dict:
    done = {p: r for p, r in report.items() if "error" not in r}
    docs = [(r[k], k in r["photo"]) for r in done.values() for k in KINDS]
    per_field = {f: [0, 0] for f in SCORED}
    groups = {"전체": [0, 0], "사진": [0, 0], "깨끗한 이미지": [0, 0]}
    dropped = 0
    for doc, photo in docs:
        for f in doc["fields"]:
            per_field[f["field"]][0] += f["ok"]
            per_field[f["field"]][1] += 1
            for g in ("전체", "사진" if photo else "깨끗한 이미지"):
                groups[g][0] += f["ok"]
                groups[g][1] += 1
            dropped += f["dropped"] is not None
    ratios = [d["ocr_ratio"] for d, _ in docs]
    seconds = [d["seconds"] for d, _ in docs]

    def detection(levels):
        exp = sum(1 for r in done.values() for lv, _ in r["expected"] if lv in levels)
        hit = exp - sum(1 for r in done.values() for lv, _ in r["missed"] if lv in levels)
        extra = sum(1 for r in done.values() for lv, _ in r["extra"] if lv in levels)
        return {"hit": hit, "expected": exp, "recall": round(hit / exp, 4) if exp else None, "extra": extra}

    return {
        "pairs_evaluated": len(done),
        "pairs_failed": len(report) - len(done),
        "field_accuracy": {g: {"correct": c, "total": t, "rate": round(c / t, 4) if t else None}
                           for g, (c, t) in groups.items()},
        "per_field": {f: {"correct": c, "total": t} for f, (c, t) in per_field.items()},
        "quotes_dropped": dropped,
        "ocr_ratio_mean": round(sum(ratios) / len(ratios), 4) if ratios else None,
        "seconds_mean": round(sum(seconds) / len(seconds), 1) if seconds else None,
        "detection_core": detection(CORE),
        "detection_minor": detection(MINOR),
        "pairs_exact": sum(1 for r in done.values() if not r["missed"] and not r["extra"]),
    }


def print_summary(s: dict, report: dict) -> None:
    fa = s["field_accuracy"]
    print(f"\n== 추출 정확도 ({len(SCORED)}개 항목 × 문서 {fa['전체']['total'] // len(SCORED)}장)")
    for g in ("전체", "깨끗한 이미지", "사진"):
        print(f"  {g:<8} {_pct(fa[g]['correct'], fa[g]['total'])}")
    print("  항목별:")
    for f, v in s["per_field"].items():
        flag = "" if v["correct"] == v["total"] else "  ←"
        print(f"    {f:<26} {v['correct']:>3}/{v['total']}{flag}")
    print(f"  인용 검증으로 버린 값: {s['quotes_dropped']}건 | OCR 원문 일치율 평균 {s['ocr_ratio_mean']}"
          f" | 문서당 평균 {s['seconds_mean']}초")

    wrong = [(p, k, f) for p, r in report.items() if "error" not in r for k in KINDS
             for f in r[k]["fields"] if not f["ok"]]
    if wrong:
        print(f"\n  틀린 항목 ({len(wrong)}건, 최대 30건 표시):")
        for p, k, f in wrong[:30]:
            why = f" [인용 폐기: {f['dropped']}]" if f["dropped"] else ""
            print(f"    {p}_{k}.{f['field']}: 추출={json.dumps(f['pred'], ensure_ascii=False)}"
                  f" / 정답={json.dumps(f['gold'], ensure_ascii=False)}{why}")

    c, m = s["detection_core"], s["detection_minor"]
    print(f"\n== 판정 ({s['pairs_evaluated']}쌍, 추출 실패 {s['pairs_failed']}쌍)")
    print(f"  불리 변경·법 기준 확인 재현율 {_pct(c['hit'], c['expected'])} | 정답에 없는 경고 {c['extra']}건")
    print(f"  누락·모호              재현율 {_pct(m['hit'], m['expected'])} | 정답에 없는 경고 {m['extra']}건")
    print(f"  경고 목록이 정답과 완전히 같은 쌍 {_pct(s['pairs_exact'], s['pairs_evaluated'])}")


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")   # Windows 콘솔 기본 cp949에서 한글·기호 깨짐 방지
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--provider", default="mock", choices=["mock", "gemini"])
    ap.add_argument("--model", default="", help="비우면 .env의 GEMINI_MODEL")
    ap.add_argument("--pairs", default="", help="쉼표로 구분 (예: pair01,pair07). 비우면 40쌍 전부")
    ap.add_argument("--sleep", type=float, default=6.0, help="실제 호출 사이 최소 간격(초)")
    ap.add_argument("--no-cache", action="store_true")
    ap.add_argument("--no-save", action="store_true", help="결과 JSON을 저장하지 않음")
    args = ap.parse_args(argv)

    answer_key = json.loads((DATA / "answer_key.json").read_text(encoding="utf-8"))
    pairs = [p.strip() for p in args.pairs.split(",") if p.strip()] or sorted(answer_key)
    extractor, model = make_extractor(args.provider, args.model)
    tag = f"{args.provider}_{model}_{EXTRACT_PROMPT_VERSION}" if args.provider != "mock" else "mock"
    sleep = 0 if args.provider == "mock" else args.sleep   # mock은 한도가 없다
    runner = CachedRunner(extractor, EVAL_DIR / "cache" / tag, use_cache=not args.no_cache, sleep=sleep)

    print(f"평가: {tag} · {len(pairs)}쌍 (합성 데이터 기준)")
    report = evaluate(runner, answer_key, pairs)
    summary = summarize(report)
    print_summary(summary, report)
    print(f"\n  호출 {runner.called}회 · 캐시 사용 {runner.cached}회")

    if not args.no_save:
        out = EVAL_DIR / "results" / f"{date.today()}_{EXTRACT_PROMPT_VERSION}_{args.provider}.json"
        out.parent.mkdir(exist_ok=True)
        meta = {"date": str(date.today()), "provider": args.provider, "model": model,
                "prompt_version": EXTRACT_PROMPT_VERSION, "pairs": pairs, "note": "합성 데이터 기준"}
        out.write_text(json.dumps({"meta": meta, "summary": summary, "pairs": report}, ensure_ascii=False, indent=1)
                       + "\n", encoding="utf-8")
        print(f"  저장: {out.relative_to(EVAL_DIR.parent)}")
    return summary


if __name__ == "__main__":
    main()
