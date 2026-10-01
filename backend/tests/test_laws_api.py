import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers.laws import get_articles

ARTICLE = {"law": "근로기준법", "article": "제17조", "title": "근로조건의 명시",
           "effective_date": "20250101", "text": "① 사용자는 근로계약을 체결할 때에..."}

client = TestClient(app)


@pytest.fixture
def articles():
    app.dependency_overrides[get_articles] = lambda: {"근로기준법 제17조": ARTICLE}
    yield
    app.dependency_overrides.clear()


def test_get_law_article(articles):
    r = client.get("/laws/근로기준법 제17조")
    assert r.status_code == 200
    assert r.json() == ARTICLE


def test_unknown_article_is_404(articles):
    assert client.get("/laws/근로기준법 제99조").status_code == 404
