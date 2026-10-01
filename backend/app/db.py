from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

# SQLite는 기본적으로 연결을 만든 스레드에서만 쓰게 막는데,
# FastAPI는 요청을 여러 스레드에서 처리하므로 이 검사를 끈다.
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """요청마다 세션을 하나 열고, 요청이 끝나면(에러가 나도) 닫는다."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
