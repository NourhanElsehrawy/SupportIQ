from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.readiness import check_database_connection
from app.db.session import get_db

router = APIRouter(prefix="/health", tags=["health"])
DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get("")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def readiness(session: DatabaseSession) -> dict[str, str]:
    try:
        check_database_connection(session)
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"code": "database_unavailable", "message": "Database is not ready."},
        ) from exc
    return {"status": "ready"}
