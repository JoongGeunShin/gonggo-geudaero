from contextlib import contextmanager
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.ai import get_explainer, get_extractor
from app.ai.base import ExplainerProvider, ExtractionError, ExtractorProvider
from app.db import get_db
from app.models import Posting
from app.schemas import BusinessCheckRequest, ComparisonRead, PostingCreate, PostingRead
from app.services.comparisons import compare_with_contract_upload
from app.services.extraction import MAX_UPLOAD_BYTES, UploadRejected
from app.services.postings import check_business, create_posting_from_upload

router = APIRouter(prefix="/postings", tags=["postings"])


@contextmanager
def upload_errors_as_http():
    """업로드·추출 흐름의 에러를 HTTP 응답으로 바꾼다."""
    try:
        yield
    except UploadRejected as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
    except ExtractionError as e:
        raise HTTPException(status_code=502, detail=str(e))   # 우리 서버가 아니라 AI 쪽 실패


@router.post("", response_model=PostingRead, status_code=201)
def create_posting(req: PostingCreate, db: Session = Depends(get_db)):
    """지원 시점의 공고를 저장한다. (추출 JSON 수동 입력. 이미지 업로드는 /postings/extract)"""
    posting = Posting(**req.model_dump(exclude={"extracted_json"}),
                      extracted_json=req.extracted_json.model_dump())
    db.add(posting)
    db.commit()
    db.refresh(posting)     # DB가 채운 id·created_at을 다시 읽어 온다
    return posting


@router.post("/extract", response_model=PostingRead, status_code=201)
def extract_posting(
    file: UploadFile = File(..., description="공고 캡처 (jpg·png·pdf, 10MB 이하)"),
    source_url: Optional[str] = Form(None, description="공고 링크 (저장만 하고 접속하지 않음)"),
    db: Session = Depends(get_db),
    extractor: ExtractorProvider = Depends(get_extractor),
):
    """공고 이미지 업로드 → 추출 → 인용검증 → 마스킹 → 저장."""
    data = file.file.read(MAX_UPLOAD_BYTES + 1)   # 한도+1까지만 읽어서 초과 여부만 안다
    with upload_errors_as_http():
        return create_posting_from_upload(db, extractor, data, file.content_type, source_url)


def get_posting_or_404(db: Session, posting_id: int) -> Posting:
    posting = db.get(Posting, posting_id)
    if posting is None:
        raise HTTPException(status_code=404, detail=f"공고를 찾을 수 없음: {posting_id}")
    return posting


@router.get("/{posting_id}", response_model=PostingRead)
def read_posting(posting_id: int, db: Session = Depends(get_db)):
    return get_posting_or_404(db, posting_id)


@router.post("/{posting_id}/business-check", response_model=PostingRead)
def business_check(posting_id: int, req: BusinessCheckRequest, db: Session = Depends(get_db)):
    """사업자번호(선택 입력)로 국세청 휴·폐업 상태를 조회해 공고에 저장한다."""
    return check_business(db, get_posting_or_404(db, posting_id), req.b_no)


@router.post("/{posting_id}/compare", response_model=ComparisonRead, status_code=201)
def compare_contract(
    posting_id: int,
    file: UploadFile = File(..., description="근로계약서 (jpg·png·pdf, 10MB 이하)"),
    db: Session = Depends(get_db),
    extractor: ExtractorProvider = Depends(get_extractor),
    explainer: ExplainerProvider = Depends(get_explainer),
):
    """계약서 이미지 업로드 → 추출 → 규칙 판정 → 설명 생성 → 저장 → 결과 반환."""
    posting = get_posting_or_404(db, posting_id)
    if posting.extracted_json is None:
        raise HTTPException(status_code=409, detail="공고 추출 결과가 없어 비교할 수 없음")
    data = file.file.read(MAX_UPLOAD_BYTES + 1)
    with upload_errors_as_http():
        return compare_with_contract_upload(db, extractor, explainer, posting, data, file.content_type)
