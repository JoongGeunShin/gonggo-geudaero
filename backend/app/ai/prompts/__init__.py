"""프롬프트는 코드 속 문자열이 아니라 파일(extract_v1.md, v2 …)로 버전 관리한다."""

from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent
EXTRACT_PROMPT_VERSION = "extract_v2"   # 바꿀 때마다 Phase 10 평가 결과를 비교 (eval/README.md)
EXPLAIN_PROMPT_VERSION = "explain_v1"


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")
