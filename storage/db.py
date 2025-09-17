from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .settings import settings


class Base(DeclarativeBase):
    pass


_engine = create_engine(settings.DATABASE_URL, future=True)
SessionLocal = sessionmaker(
    bind=_engine, autoflush=False, autocommit=False, future=True
)


def get_session() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db() -> Iterator[Session]:
    yield from get_session()
