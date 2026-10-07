"""가짜 구현: AI를 부르지 않는다. 비용 0원으로 전체 흐름을 만들고 테스트할 때 쓴다.

- MockExtractor: samples/*.json 정답을 돌려준다.
- MockExplainer: 등급별 고정 문구로 설명·질문을 만든다.
"""

import hashlib
from pathlib import Path

from app.ai.base import DocKind, ExtractionResult
from app.schemas import ConditionDoc, Explanation, ExplanationItem, Finding

SAMPLES_DIR = Path(__file__).resolve().parents[3] / "samples"   # backend/app/ai → 저장소 루트/samples


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _full_text(doc: ConditionDoc) -> str:
    """정답 JSON에는 OCR 원문이 없으므로, 인용들을 이어 붙여 원문 대신 쓴다 (인용 검증을 통과하도록)."""
    quotes = [field.quote for field in doc.__dict__.values() if field.quote]
    return "\n".join(dict.fromkeys(quotes))   # 순서 유지한 채 중복 제거


class MockExtractor:
    """샘플 이미지면 그 정답을, 처음 보는 이미지면 같은 종류의 case1 정답을 돌려준다."""

    def __init__(self, samples_dir: Path = SAMPLES_DIR):
        self.samples_dir = samples_dir
        # 이미지 내용(해시) → 정답 JSON 경로. 인터페이스가 파일명이 아닌 bytes를 받으므로 내용으로 찾는다.
        self._by_hash = {
            _sha256(png.read_bytes()): png.with_suffix(".json")
            for png in samples_dir.glob("*.png")
            if png.with_suffix(".json").exists()
        }

    def extract(self, image_bytes: bytes, media_type: str, doc_kind: DocKind) -> ExtractionResult:
        path = self._by_hash.get(_sha256(image_bytes)) or self.samples_dir / f"case1_{doc_kind}.json"
        if not path.exists():
            return ExtractionResult(full_text="")
        doc = ConditionDoc.model_validate_json(path.read_text(encoding="utf-8"))
        return ExtractionResult(full_text=_full_text(doc), fields=doc)


TEMPLATE_VERSION = "template_v1"

# 등급별 질문 틀. LLM 없이도 질문이 나오게 하고, Gemini 결과가 쓸 수 없을 때 대신 쓴다.
QUESTION_TEMPLATES = {
    "불리 변경": "공고에서 본 '{item}' 조건과 계약서 내용이 다른데, 어느 쪽이 맞는지 확인해 주실 수 있을까요?",
    "법 기준 확인": "계약서의 '{item}' 조건이 어떤 기준으로 정해졌는지 확인해 주실 수 있을까요?",
    "누락": "계약서에 '{item}' 내용이 없는데, 계약서에 적어 주실 수 있을까요?",
    "모호": "'{item}'의 구체적인 기준을 계약서에 적어 주실 수 있을까요?",
}


def template_item(finding: Finding) -> ExplanationItem:
    """판정 결과 한 건 → 고정 문구 설명. summary는 엔진 메시지를 그대로 쓴다 (새 사실을 만들지 않음)."""
    return ExplanationItem(
        item=finding.item,
        summary=finding.message,
        question=QUESTION_TEMPLATES[finding.level].format(item=finding.item),
    )


def to_explain(findings: list[Finding]) -> list[Finding]:
    """설명할 대상: '동일·유리'는 물어볼 게 없으므로 뺀다."""
    return [f for f in findings if f.level != "동일·유리"]


class MockExplainer:
    """가짜 설명기: AI를 부르지 않고 등급별 고정 문구로 질문을 만든다. 테스트와 Gemini 실패 시 대체용."""

    def explain(self, findings: list[Finding]) -> Explanation:
        return Explanation(prompt_version=TEMPLATE_VERSION,
                           items=[template_item(f) for f in to_explain(findings)])
