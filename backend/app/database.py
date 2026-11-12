"""SQLAlchemy engine, session factory, declarative base, and DB dependency."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# create_engine is called once at module load time.
# For testing, the DATABASE_URL env var is set to SQLite before this module
# is first imported (see tests/conftest.py).
engine = create_engine(
    settings.database_url,
    # psycopg2 uses connection pooling by default; fine for Day 1.
    # SQLite (tests) needs check_same_thread=False — harmless on Postgres.
    connect_args=(
        {"check_same_thread": False}
        if settings.database_url.startswith("sqlite")
        else {}
    ),
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Single shared declarative base.

    All models inherit from this so that Alembic can discover them via
    ``target_metadata = Base.metadata`` in alembic/env.py.
    """


def get_db():
    """FastAPI dependency — yields a DB session per request, then closes it."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
