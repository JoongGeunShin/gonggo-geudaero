"""Gemini 설명 단계 연습: 샘플 정답 JSON으로 판정한 결과를 실제 Gemini에 보내 설명·질문을 확인한다.

    python scripts/try_explain.py           # case1
    python scripts/try_explain.py case3

이미지는 보내지 않고 판정 결과(글자)만 보내므로 한 번에 몇 초 정도 걸린다.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))   # backend/ 를 import 경로에
from app.ai.gemini import GeminiExplainer  # noqa: E402
from app.ai.wording import assertive_words  # noqa: E402
from app.config import settings  # noqa: E402
from app.rules.engine import compare  # noqa: E402
from app.schemas import ConditionDoc  # noqa: E402

SAMPLES = Path(__file__).resolve().parents[2] / "samples"


def load(case: str, kind: str) -> ConditionDoc:
    return ConditionDoc.model_validate_json((SAMPLES / f"{case}_{kind}.json").read_text(encoding="utf-8"))


def main(case: str = "case1") -> None:
    sys.stdout.reconfigure(encoding="utf-8")   # Windows 콘솔에서 한글이 깨지지 않게
    model = settings.gemini_explain_model or settings.gemini_model
    findings = compare(load(case, "posting"), load(case, "contract"))
    explanation = GeminiExplainer(api_key=settings.gemini_api_key, model=model).explain(findings)
    print(f"model={model} prompt={explanation.prompt_version}\n")
    for item in explanation.items:
        print(f"[{item.item}]\n  설명: {item.summary}\n  질문: {item.question}")
        if words := assertive_words(item.summary + item.question):
            print(f"  ⚠ 단정 표현: {words}")


if __name__ == "__main__":
    main(*sys.argv[1:])
