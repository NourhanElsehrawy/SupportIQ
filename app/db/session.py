from collections.abc import Generator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def create_database_engine(database_url: str) -> Engine:
    """Create the process-wide SQLAlchemy engine and connection pool."""
    return create_engine(database_url, pool_pre_ping=True)


engine = create_database_engine(settings.database_url)

SessionFactory = sessionmaker(
    bind=engine,
    class_=Session,
    autoflush=False,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """Provide one database session for the lifetime of a request."""
    session = SessionFactory()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
