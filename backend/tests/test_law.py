import json

import pytest

from app.external.law import basis_keys, get_article, load_law_articles

ARTICLE = {"law": "근로기준법", "article": "제17조", "title": "근로조건의 명시",
           "effective_date": "20250101", "text": "① 사용자는 근로계약을 체결할 때에..."}


@pytest.fixture
def law_file(tmp_path):
    path = tmp_path / "law_articles.json"
    data = {"fetched_at": "2026-10-01", "source": "test", "articles": {"근로기준법 제17조": ARTICLE}}
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


def test_load_returns_articles_by_key(law_file):
    assert load_law_articles(law_file) == {"근로기준법 제17조": ARTICLE}


def test_missing_file_returns_empty(tmp_path):
    assert load_law_articles(tmp_path / "없음.json") == {}


def test_get_article(law_file):
    articles = load_law_articles(law_file)
    assert get_article("근로기준법 제17조", articles)["title"] == "근로조건의 명시"
    assert get_article("근로기준법 제99조", articles) is None


@pytest.mark.parametrize("basis, keys", [
    ("근로기준법 제20조", ["근로기준법 제20조"]),
    ("근로기준법 제17조·제60조", ["근로기준법 제17조", "근로기준법 제60조"]),
    ("최저임금법 제5조②, 같은 법 시행령 제3조", ["최저임금법 제5조", "최저임금법 시행령 제3조"]),
    ("근로기준법 시행령 제27조의2", ["근로기준법 시행령 제27조의2"]),
    ("", []),
])
def test_basis_keys(basis, keys):
    assert basis_keys(basis) == keys
