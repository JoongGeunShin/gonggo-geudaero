from fastapi import APIRouter

from app.rules.engine import compare
from app.schemas import CompareRequest, Finding

router = APIRouter(prefix="/rules", tags=["rules"])


@router.post("/compare", response_model=list[Finding])
def compare_documents(req: CompareRequest):
    """공고·계약서 JSON을 받아 규칙 엔진 판정 결과를 돌려준다 (AI 없이 규칙만)."""
    return compare(req.posting, req.contract)
