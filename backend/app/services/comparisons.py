"""공고 ↔ 계약서 대조 흐름: 계약서 추출 → 문서 저장 → 규칙 판정 → 설명 생성 → 결과 저장."""

import logging

from sqlalchemy.orm import Session

from app.ai.base import ExplainerProvider, ExplanationError, ExtractorProvider
from app.ai.mock import MockExplainer
from app.models import Comparison, Document, Posting
from app.rules.engine import compare
from app.schemas import ConditionDoc, Explanation, Finding
from app.services.extraction import extract_document

logger = logging.getLogger(__name__)


def explain_findings(explainer: ExplainerProvider, findings: list[Finding]) -> Explanation:
    """설명은 덤이다. AI 설명이 실패해도 판정 결과는 보여줘야 하므로 고정 문구로 대신한다."""
    try:
        return explainer.explain(findings)
    except ExplanationError as e:
        logger.warning("설명 생성 실패, 고정 문구로 대체: %s", e)
        return MockExplainer().explain(findings)


def compare_with_contract_upload(db: Session, extractor: ExtractorProvider, explainer: ExplainerProvider,
                                 posting: Posting, data: bytes, media_type: str) -> Comparison:
    """판정은 규칙 엔진만 한다. AI는 계약서를 읽고, 판정 결과를 쉬운 말로 옮기는 데만 쓴다."""
    result = extract_document(extractor, data, media_type, "contract")
    document = Document(
        posting_id=posting.id,
        doc_type="contract",
        raw_text=result.full_text,
        extracted_json=result.fields.model_dump(),
        extracted_by=result.extracted_by,
    )
    db.add(document)
    db.flush()   # commit 전에 document.id를 받아 온다

    findings = compare(ConditionDoc.model_validate(posting.extracted_json), result.fields)
    comparison = Comparison(
        posting_id=posting.id,
        document_id=document.id,
        findings_json=[f.model_dump() for f in findings],
        explanation_json=explain_findings(explainer, findings).model_dump(),
    )
    db.add(comparison)
    db.commit()
    db.refresh(comparison)
    return comparison
