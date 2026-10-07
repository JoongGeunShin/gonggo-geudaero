"""여러 API 테스트가 같이 쓰는 픽스처."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401  Base.metadata에 테이블 등록
from app.ai import get_explainer, get_extractor
from app.ai.mock import MockExplainer, MockExtractor
from app.db import Base, get_db
from app.main import app


@pytest.fixture
def client():
    # 인메모리 SQLite는 연결마다 DB가 새로 생기므로, StaticPool로 연결 하나를 모든 요청이 같이 쓰게 한다
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, expire_on_commit=False)

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    # .env의 AI_PROVIDER와 상관없이 테스트는 항상 가짜 추출기·설명기 (Gemini를 부르지 않음)
    app.dependency_overrides[get_extractor] = MockExtractor
    app.dependency_overrides[get_explainer] = MockExplainer
    yield TestClient(app)
    app.dependency_overrides.clear()
