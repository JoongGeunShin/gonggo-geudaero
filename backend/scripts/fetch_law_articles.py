"""법제처 DRF API에서 서비스가 쓰는 조문만 받아 data/law_articles.json으로 저장한다.

조문은 자주 바뀌지 않으므로 요청마다 부르지 않고, 이 스크립트를 가끔 한 번 돌린다.
실행 (backend 폴더에서, .env에 LAW_OC 필요):
    python -m scripts.fetch_law_articles
"""

import json
from datetime import date
from pathlib import Path

import httpx

from app.config import settings
from app.external.law import LAW_PATH

SEARCH_URL = "http://www.law.go.kr/DRF/lawSearch.do"
SERVICE_URL = "http://www.law.go.kr/DRF/lawService.do"

NEEDED = {
    "채용절차의 공정화에 관한 법률": ["제3조", "제4조"],
    "근로기준법": ["제17조", "제20조", "제60조"],
    "근로기준법 시행령": ["제27조의2"],
    "최저임금법": ["제5조", "제6조"],
    "최저임금법 시행령": ["제3조"],
}


def _as_list(x):
    """DRF JSON은 항목이 하나면 리스트 대신 객체를 주므로 항상 리스트로 맞춘다."""
    if x is None:
        return []
    return x if isinstance(x, list) else [x]


def _text(x):
    return "\n".join(_text(i) for i in x) if isinstance(x, list) else (x or "").strip()


def jo_code(article: str) -> str:
    """'제27조의2' → '002702' (조번호 4자리 + 가지번호 2자리)."""
    main, _, branch = article.removeprefix("제").partition("조")
    return f"{int(main):04d}{int(branch.removeprefix('의') or 0):02d}"


def find_mst(client: httpx.Client, law_name: str) -> str:
    r = client.get(SEARCH_URL, params={"OC": settings.law_oc, "target": "law", "type": "JSON", "query": law_name})
    r.raise_for_status()
    for item in _as_list(r.json()["LawSearch"].get("law")):
        if item["법령명한글"] == law_name:
            return item["법령일련번호"]
    raise LookupError(f"법령을 찾지 못함: {law_name}")


def fetch_article(client: httpx.Client, mst: str, article: str) -> dict:
    r = client.get(SERVICE_URL, params={"OC": settings.law_oc, "target": "law", "type": "JSON",
                                        "MST": mst, "JO": jo_code(article)})
    r.raise_for_status()
    law = r.json()["법령"]
    info = law["기본정보"]
    unit = next(u for u in _as_list(law["조문"]["조문단위"]) if u.get("조문여부") == "조문")
    lines = [_text(unit.get("조문내용"))]
    for hang in _as_list(unit.get("항")):
        lines.append(_text(hang.get("항내용")))
        for ho in _as_list(hang.get("호")):
            lines.append(_text(ho.get("호내용")))
            lines += [_text(mok.get("목내용")) for mok in _as_list(ho.get("목"))]
    return {
        "law": info["법령명_한글"],
        "article": article,
        "title": unit.get("조문제목", ""),
        "effective_date": info["시행일자"],
        "text": "\n".join(line for line in lines if line),
    }


def main():
    if not settings.law_oc:
        raise SystemExit("LAW_OC가 .env에 없습니다.")
    articles = {}
    with httpx.Client(timeout=10) as client:
        for law_name, wanted in NEEDED.items():
            mst = find_mst(client, law_name)
            for article in wanted:
                articles[f"{law_name} {article}"] = fetch_article(client, mst, article)
                print("OK", law_name, article)
    out = {"fetched_at": date.today().isoformat(), "source": SERVICE_URL, "articles": articles}
    LAW_PATH.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{len(articles)}개 조문 저장 → {LAW_PATH}")


if __name__ == "__main__":
    main()
