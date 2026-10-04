"""공고 ↔ 계약서 대조 흐름: 계약서 추출 → 문서 저장 → 규칙 판정 → 결과 저장."""

from sqlalchemy.orm import Session

from app.ai.base import ExtractorProvider
from app.models import Comparison, Document, Posting
from app.rules.engine import compare
from app.schemas import ConditionDoc
from app.services.extraction import extract_document


def compare_with_contract_upload(db: Session, extractor: ExtractorProvider, posting: Posting,
                                 data: bytes, media_type: str) -> Comparison:
    """판정은 규칙 엔진만 한다. AI는 계약서를 읽는 데까지만 쓴다."""
    result = extract_document(extractor, data, media_type, "contract")
    document = Document(
        posting_id=posting.id,
        doc_type="contract",
        raw_text=result.full_text,
        extracted_json=result.fields.model_dump(),
    )
    db.add(document)
    db.flush()   # commit 전에 document.id를 받아 온다

    findings = compare(ConditionDoc.model_validate(posting.extracted_json), result.fields)
    comparison = Comparison(
        posting_id=posting.id,
        document_id=document.id,
        findings_json=[f.model_dump() for f in findings],
    )
    db.add(comparison)
    db.commit()
    db.refresh(comparison)
    return comparison
