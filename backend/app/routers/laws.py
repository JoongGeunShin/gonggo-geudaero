from fastapi import APIRouter, Depends, HTTPException

from app.external.law import get_article, load_law_articles

router = APIRouter(prefix="/laws", tags=["laws"])


def get_articles() -> dict[str, dict]:
    """조문 캐시. 테스트에서는 dependency_overrides로 바꿔 끼운다."""
    return load_law_articles()


@router.get("/{key}")
def read_law_article(key: str, articles: dict = Depends(get_articles)):
    """판정 근거 키(예: '근로기준법 제17조')로 조문 원문을 돌려준다."""
    article = get_article(key, articles)
    if article is None:
        raise HTTPException(status_code=404, detail=f"조문을 찾을 수 없음: {key}")
    return article
