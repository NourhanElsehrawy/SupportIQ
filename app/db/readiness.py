from sqlalchemy import text
from sqlalchemy.orm import Session


def check_database_connection(session: Session) -> None:
    """Raise a SQLAlchemy exception when PostgreSQL cannot answer a trivial query."""
    session.execute(text("SELECT 1"))
