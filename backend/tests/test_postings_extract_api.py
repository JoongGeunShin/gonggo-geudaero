"""POST /postings/extract: 공고 이미지 업로드 → 추출 → 인용검증 → 마스킹 → 저장."""

from pathlib import Path

import pytest

from app.ai import get_extractor
from app.ai.base import ExtractionError, ExtractionResult
from app.main import app
from app.schemas import ConditionDoc, ExtractedField
from app.services.extraction import MAX_UPLOAD_BYTES

SAMPLES = Path(__file__).resolve().parents[2] / "samples"


def upload(client, name="case2_posting.png", data=None, media_type="image/png", **form):
    data = (SAMPLES / name).read_bytes() if data is None else data
    return client.post("/postings/extract", files={"file": (name, data, media_type)}, data=form)


class FakeExtractor:
    """정해 둔 결과를 그대로 돌려주는 추출기."""

    def __init__(self, result=None, error=None):
        self.result, self.error = result, error

    def extract(self, image_bytes, media_type, doc_kind):
        if self.error:
            raise self.error
        return self.result


@pytest.fixture
def use_extractor():
    def _use(extractor):
        app.dependency_overrides[get_extractor] = lambda: extractor
    return _use


def test_extracts_and_saves_sample_posting(client):
    r = upload(client)
    assert r.status_code == 201
    posting = r.json()
    expected = ConditionDoc.model_validate_json((SAMPLES / "case2_posting.json").read_text(encoding="utf-8"))
    assert posting["source_type"] == "capture"
    assert posting["extracted_json"]["wage"] == expected.wage.model_dump()
    assert posting["company_name"] == expected.company.value
    assert posting["raw_text"]

    assert client.get(f"/postings/{posting['id']}").json() == posting


def test_keeps_source_url(client):
    r = upload(client, source_url="https://example.com/jobs/1")
    assert r.json()["source_url"] == "https://example.com/jobs/1"


def test_rejects_unsupported_media_type(client):
    assert upload(client, name="a.txt", data=b"hello", media_type="text/plain").status_code == 415


def test_rejects_too_large_file(client):
    assert upload(client, data=b"0" * (MAX_UPLOAD_BYTES + 1)).status_code == 413


def test_rejects_empty_file(client):
    assert upload(client, data=b"").status_code == 400


def test_drops_values_whose_quote_is_not_in_text(client, use_extractor):
    fields = ConditionDoc(wage=ExtractedField(value={"type": "월급", "amount_min": 3000000}, quote="월 300만원"))
    use_extractor(FakeExtractor(ExtractionResult(full_text="월 250만원", fields=fields)))

    wage = upload(client).json()["extracted_json"]["wage"]
    assert wage["value"] is None
    assert wage["verification"] == "quote_not_found"


def test_masks_personal_info_before_saving(client, use_extractor):
    fields = ConditionDoc(company=ExtractedField(value="테스트상사", quote="테스트상사 담당 010-1234-5678"))
    text = "테스트상사 담당 010-1234-5678"
    use_extractor(FakeExtractor(ExtractionResult(full_text=text, fields=fields)))

    posting = upload(client).json()
    assert "010-1234-5678" not in posting["raw_text"]
    assert "010-1234-5678" not in posting["extracted_json"]["company"]["quote"]
    assert posting["extracted_json"]["company"]["value"] == "테스트상사"   # 값은 남는다


def test_extraction_failure_returns_502(client, use_extractor):
    use_extractor(FakeExtractor(error=ExtractionError("Gemini 호출 실패 (429)")))
    r = upload(client)
    assert r.status_code == 502
    assert "429" in r.json()["detail"]
