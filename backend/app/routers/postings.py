from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Posting
from app.schemas import PostingCreate, PostingRead

router = APIRouter(prefix="/postings", tags=["postings"])


@router.post("", response_model=PostingRead, status_code=201)
def create_posting(req: PostingCreate, db: Session = Depends(get_db)):
    """지원 시점의 공고를 저장한다. (지금은 추출 JSON 수동 입력, 이미지 업로드는 Phase 7)"""
    posting = Posting(**req.model_dump(exclude={"extracted_json"}),
                      extracted_json=req.extracted_json.model_dump())
    db.add(posting)
    db.commit()
    db.refresh(posting)     # DB가 채운 id·created_at을 다시 읽어 온다
    return posting


@router.get("/{posting_id}", response_model=PostingRead)
def read_posting(posting_id: int, db: Session = Depends(get_db)):
    posting = db.get(Posting, posting_id)
    if posting is None:
        raise HTTPException(status_code=404, detail=f"공고를 찾을 수 없음: {posting_id}")
    return posting
