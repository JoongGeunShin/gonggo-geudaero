"""가짜 추출기: AI를 부르지 않고 samples/*.json 정답을 돌려준다. 비용 0원으로 전체 흐름을 만들 때 쓴다."""

import hashlib
from pathlib import Path

from app.ai.base import DocKind, ExtractionResult
from app.schemas import ConditionDoc

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
