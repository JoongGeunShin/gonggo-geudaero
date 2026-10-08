"""공고 저장 흐름. 라우터는 HTTP만 다루고, 무엇을 어떤 순서로 하는지는 여기서 정한다."""

from sqlalchemy.orm import Session

from app.ai.base import ExtractorProvider
from app.external.nts import get_business_status
from app.models import Posting
from app.services.extraction import extract_document


def create_posting_from_upload(db: Session, extractor: ExtractorProvider, data: bytes, media_type: str,
                               source_url: str | None = None) -> Posting:
    """공고 캡처 한 장을 추출해 저장한다. 원본 이미지는 저장하지 않는다 (image_path=None)."""
    result = extract_document(extractor, data, media_type, "posting")
    company = result.fields.company.value
    posting = Posting(
        source_type="capture",
        source_url=source_url,
        raw_text=result.full_text,
        extracted_json=result.fields.model_dump(),
        extracted_by=result.extracted_by,
        company_name=company if isinstance(company, str) else None,
    )
    db.add(posting)
    db.commit()
    db.refresh(posting)
    return posting


def check_business(db: Session, posting: Posting, b_no: str) -> Posting:
    """국세청 상태를 조회해 공고에 붙인다. 조회 실패(None)도 '확인 불가'로 그대로 저장한다."""
    posting.b_no = b_no
    posting.nts_status_json = get_business_status(b_no)
    db.commit()
    db.refresh(posting)
    return posting
