import pytest

from scripts.fetch_law_articles import jo_code


@pytest.mark.parametrize("article, code", [("제17조", "001700"), ("제27조의2", "002702"), ("제3조", "000300")])
def test_jo_code(article, code):
    assert jo_code(article) == code
