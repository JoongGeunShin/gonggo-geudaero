from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Comparison
from app.schemas import ComparisonRead

router = APIRouter(prefix="/comparisons", tags=["comparisons"])


@router.get("/{comparison_id}", response_model=ComparisonRead)
def read_comparison(comparison_id: int, db: Session = Depends(get_db)):
    """저장된 대조 결과를 다시 본다 (결과 화면 새로고침·공유 링크용)."""
    comparison = db.get(Comparison, comparison_id)
    if comparison is None:
        raise HTTPException(status_code=404, detail=f"대조 결과를 찾을 수 없음: {comparison_id}")
    return comparison
