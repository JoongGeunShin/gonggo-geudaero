"""POST /postings/{id}/compare: 계약서 업로드 → 추출 → 규칙 판정 → 저장."""

import json
from pathlib import Path

import pytest

from app.ai import get_explainer, get_extractor
from app.ai.base import ExplanationError, ExtractionError
from app.main import app
from app.rules.engine import AMBER, RED

SAMPLES = Path(__file__).resolve().parents[2] / "samples"
ANSWER_KEY = json.loads((SAMPLES / "answer_key.json").read_text(encoding="utf-8"))


def upload_posting(client, case):
    data = (SAMPLES / f"{case}_posting.png").read_bytes()
    return client.post("/postings/extract", files={"file": ("p.png", data, "image/png")}).json()["id"]


def upload_contract(client, posting_id, case="case2", data=None, media_type="image/png"):
    data = (SAMPLES / f"{case}_contract.png").read_bytes() if data is None else data
    return client.post(f"/postings/{posting_id}/compare", files={"file": ("c.png", data, media_type)})


@pytest.mark.parametrize("case", sorted(ANSWER_KEY))
def test_two_images_give_expected_flags(client, case):
    posting_id = upload_posting(client, case)
    r = upload_contract(client, posting_id, case)
    assert r.status_code == 201

    result = r.json()
    assert result["posting_id"] == posting_id
    assert result["document_id"] > 0
    assert result["contract_extracted_by"] == "mock"
    found = {(f["level"], f["item"]) for f in result["findings_json"] if f["level"] in (RED, AMBER)}
    assert found == {(e["level"], e["item"]) for e in ANSWER_KEY[case]["expected_flags"]}


def test_missing_posting_returns_404(client):
    assert upload_contract(client, 999).status_code == 404


def test_rejects_unsupported_media_type(client):
    posting_id = upload_posting(client, "case2")
    assert upload_contract(client, posting_id, data=b"hello", media_type="text/plain").status_code == 415


def test_extraction_failure_returns_502(client):
    posting_id = upload_posting(client, "case2")

    class Failing:
        def extract(self, image_bytes, media_type, doc_kind):
            raise ExtractionError("Gemini 응답 시간 초과 (120초)")

    app.dependency_overrides[get_extractor] = Failing
    assert upload_contract(client, posting_id).status_code == 502


def test_result_includes_question_for_every_flag(client):
    posting_id = upload_posting(client, "case2")
    result = upload_contract(client, posting_id).json()
    flagged = [f["item"] for f in result["findings_json"] if f["level"] != "동일·유리"]
    assert [i["item"] for i in result["explanation_json"]["items"]] == flagged
    assert all(i["question"] for i in result["explanation_json"]["items"])


def test_explanation_failure_falls_back_to_templates(client):
    posting_id = upload_posting(client, "case2")

    class Failing:
        def explain(self, findings):
            raise ExplanationError("Gemini 호출 실패 (503)")

    app.dependency_overrides[get_explainer] = Failing
    r = upload_contract(client, posting_id)
    assert r.status_code == 201   # 설명이 실패해도 판정 결과는 저장·반환
    assert r.json()["explanation_json"]["prompt_version"] == "template_v1"


def test_saved_comparison_keeps_explanation(client):
    posting_id = upload_posting(client, "case2")
    created = upload_contract(client, posting_id).json()
    again = client.get(f"/comparisons/{created['id']}").json()
    assert again["explanation_json"] == created["explanation_json"]
