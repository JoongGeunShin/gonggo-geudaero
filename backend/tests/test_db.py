from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_db


def test_get_db_yields_working_session():
    gen = get_db()
    db = next(gen)
    assert isinstance(db, Session)
    assert db.execute(text("SELECT 1")).scalar() == 1
    gen.close()
