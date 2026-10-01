import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401  Base.metadata에 테이블 등록
from app.db import Base, get_db
from app.main import app


@pytest.fixture
def client():
    # 인메모리 SQLite는 연결마다 DB가 새로 생기므로, StaticPool로 연결 하나를 모든 요청이 같이 쓰게 한다
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, expire_on_commit=False)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_create_then_read_posting(client):
    body = {
        "source_type": "manual",
        "company_name": "테스트상사",
        "b_no": "1248100998",
        "extracted_json": {"wage": {"value": {"type": "시급", "amount_min": 10320}, "quote": "시급 10,320원"}},
    }
    created = client.post("/postings", json=body)
    assert created.status_code == 201
    posting = created.json()
    assert posting["id"] > 0
    assert posting["created_at"]

    read = client.get(f"/postings/{posting['id']}")
    assert read.status_code == 200
    assert read.json() == posting
    assert read.json()["extracted_json"]["wage"]["quote"] == "시급 10,320원"


def test_read_missing_posting_returns_404(client):
    assert client.get("/postings/999").status_code == 404


def test_rejects_unknown_source_type(client):
    assert client.post("/postings", json={"source_type": "fax", "extracted_json": {}}).status_code == 422


def test_rejects_extracted_json_not_matching_schema(client):
    r = client.post("/postings", json={"source_type": "manual", "extracted_json": {"unknown_field": {}}})
    assert r.status_code == 422
