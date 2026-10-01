"""법령 조문 원문 — scripts/fetch_law_articles.py가 받아 둔 JSON 캐시에서 읽는다."""

import json
import re
from pathlib import Path

LAW_PATH = Path(__file__).resolve().parents[2] / "data" / "law_articles.json"

ARTICLE_RE = re.compile(r"제\d+조(?:의\d+)?")


def load_law_articles(path: Path = LAW_PATH) -> dict[str, dict]:
    """{'근로기준법 제17조': {law, article, title, effective_date, text}}. 캐시가 없으면 빈 dict."""
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))["articles"]


def get_article(key: str, articles: dict[str, dict]) -> dict | None:
    return articles.get(key)


def basis_keys(basis: str) -> list[str]:
    """판정 근거 문자열을 조문 키 목록으로 나눈다.

    '최저임금법 제5조②, 같은 법 시행령 제3조' → ['최저임금법 제5조', '최저임금법 시행령 제3조']
    """
    keys, prev_law = [], ""
    for part in filter(None, (p.strip() for p in basis.split(","))):
        first = ARTICLE_RE.search(part)
        if not first:
            continue
        law = part[:first.start()].strip()
        if law.startswith("같은 법"):
            law = (prev_law + law.removeprefix("같은 법")).strip()
        keys += [f"{law} {a}" for a in ARTICLE_RE.findall(part)]
        prev_law = law
    return keys
