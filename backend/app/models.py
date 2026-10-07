"""DB 테이블 정의. 로그인 없는 MVP라 사용자 테이블은 두지 않는다."""

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Posting(Base):
    """지원 시점에 저장한 채용공고."""

    __tablename__ = "postings"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    source_type: Mapped[str] = mapped_column(String(20))        # capture | url | manual
    source_url: Mapped[str | None] = mapped_column(String(2000))
    image_path: Mapped[str | None] = mapped_column(String(500))
    raw_text: Mapped[str | None] = mapped_column(Text)
    extracted_json: Mapped[dict | None] = mapped_column(JSON)    # ConditionDoc
    company_name: Mapped[str | None] = mapped_column(String(200))
    b_no: Mapped[str | None] = mapped_column(String(10))         # 사업자등록번호, 하이픈 없이
    nts_status_json: Mapped[dict | None] = mapped_column(JSON)   # 국세청 상태조회 응답


class Document(Base):
    """공고와 비교할 근로계약서·임금명세서."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    posting_id: Mapped[int] = mapped_column(ForeignKey("postings.id"))
    doc_type: Mapped[str] = mapped_column(String(20))            # contract | payslip
    image_path: Mapped[str | None] = mapped_column(String(500))
    raw_text: Mapped[str | None] = mapped_column(Text)
    extracted_json: Mapped[dict | None] = mapped_column(JSON)    # ConditionDoc
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Comparison(Base):
    """공고 ↔ 문서 대조 결과."""

    __tablename__ = "comparisons"

    id: Mapped[int] = mapped_column(primary_key=True)
    posting_id: Mapped[int] = mapped_column(ForeignKey("postings.id"))
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    findings_json: Mapped[list] = mapped_column(JSON)            # list[Finding]
    explanation_json: Mapped[dict | None] = mapped_column(JSON)  # Explanation (설명·질문)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
