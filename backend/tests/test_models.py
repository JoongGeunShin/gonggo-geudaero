import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db import Base
from app.models import Comparison, Document, Posting


@pytest.fixture
def db():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_posting_document_comparison_roundtrip(db):
    posting = Posting(source_type="manual", company_name="테스트상사", b_no="1248100998",
                      extracted_json={"hourly_wage": {"value": 10320}})
    db.add(posting)
    db.flush()
    document = Document(posting_id=posting.id, doc_type="contract",
                        extracted_json={"hourly_wage": {"value": 9000}})
    db.add(document)
    db.flush()
    db.add(Comparison(posting_id=posting.id, document_id=document.id,
                      findings_json=[{"rule": "wage_lower", "level": "RED"}]))
    posting_id, document_id = posting.id, document.id
    db.commit()
    db.expunge_all()    # 메모리에 남은 객체를 버리고 DB에서 새로 읽게 한다

    saved = db.get(Posting, posting_id)
    assert saved.created_at is not None
    assert saved.extracted_json == {"hourly_wage": {"value": 10320}}
    comparison = db.query(Comparison).one()
    assert comparison.document_id == document_id
    assert comparison.findings_json[0]["level"] == "RED"
    assert comparison.explanation_json is None
