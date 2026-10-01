import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

SAMPLES = Path(__file__).resolve().parents[2] / "samples"
client = TestClient(app)


def sample(name):
    return json.loads((SAMPLES / f"{name}.json").read_text(encoding="utf-8"))


def test_compare_returns_findings_for_sample_pair():
    r = client.post("/rules/compare", json={"posting": sample("case2_posting"), "contract": sample("case2_contract")})
    assert r.status_code == 200
    flagged = {(f["level"], f["item"]) for f in r.json() if f["level"] in ("불리 변경", "법 기준 확인")}
    assert flagged == {("불리 변경", "임금(월 환산)"), ("불리 변경", "임금(기본 시급)")}


def test_compare_response_has_finding_fields():
    r = client.post("/rules/compare", json={"posting": sample("case2_posting"), "contract": sample("case2_contract")})
    first = r.json()[0]
    assert set(first) == {"level", "item", "message", "posting_quote", "contract_quote", "basis"}


def test_empty_documents_are_accepted():
    # 모든 항목이 기본값(None)이라도 판정은 돌아가야 함 → 누락·모호 + 동일·유리
    r = client.post("/rules/compare", json={"posting": {}, "contract": {}})
    assert r.status_code == 200
    assert any(f["level"] == "동일·유리" for f in r.json())


def test_typo_field_is_rejected_with_422():
    r = client.post("/rules/compare", json={"posting": {"wgae": {"value": 1}}, "contract": {}})
    assert r.status_code == 422


def test_missing_contract_is_rejected_with_422():
    r = client.post("/rules/compare", json={"posting": {}})
    assert r.status_code == 422
