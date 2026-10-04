"""공고 저장 흐름. 라우터는 HTTP만 다루고, 무엇을 어떤 순서로 하는지는 여기서 정한다."""

from sqlalchemy.orm import Session

from app.ai.base import ExtractorProvider
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
        company_name=company if isinstance(company, str) else None,
    )
    db.add(posting)
    db.commit()
    db.refresh(posting)
    return posting
