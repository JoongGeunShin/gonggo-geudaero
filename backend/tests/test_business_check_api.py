"""POST /postings/{id}/business-check: 사업자번호로 국세청 상태조회 후 공고에 저장."""

import pytest

from app.services import postings as posting_service

STATUS_OK = {"b_no": "1248100998", "b_stt": "계속사업자", "b_stt_cd": "01"}


@pytest.fixture
def posting_id(client):
    r = client.post("/postings", json={"source_type": "manual", "extracted_json": {}})
    return r.json()["id"]


@pytest.fixture
def nts(monkeypatch):
    """국세청 호출을 가짜로 바꾸고, 어떤 번호로 불렸는지 기록한다."""
    calls = []

    def fake(b_no):
        calls.append(b_no)
        return fake.result

    fake.result = STATUS_OK
    fake.calls = calls
    monkeypatch.setattr(posting_service, "get_business_status", fake)
    return fake


def test_saves_number_and_status(client, posting_id, nts):
    r = client.post(f"/postings/{posting_id}/business-check", json={"b_no": "124-81-00998"})
    assert r.status_code == 200
    assert r.json()["b_no"] == "1248100998"
    assert r.json()["nts_status_json"]["b_stt_cd"] == "01"
    assert nts.calls == ["1248100998"]

    saved = client.get(f"/postings/{posting_id}").json()
    assert saved["nts_status_json"] == STATUS_OK


def test_unavailable_status_is_saved_as_null(client, posting_id, nts):
    nts.result = None   # 키 없음·국세청 장애 → '확인 불가'
    r = client.post(f"/postings/{posting_id}/business-check", json={"b_no": "1248100998"})
    assert r.status_code == 200
    assert r.json()["b_no"] == "1248100998"
    assert r.json()["nts_status_json"] is None


def test_rejects_malformed_number(client, posting_id, nts):
    r = client.post(f"/postings/{posting_id}/business-check", json={"b_no": "12345"})
    assert r.status_code == 422
    assert nts.calls == []


def test_missing_posting_returns_404(client, nts):
    assert client.post("/postings/999/business-check", json={"b_no": "1248100998"}).status_code == 404
