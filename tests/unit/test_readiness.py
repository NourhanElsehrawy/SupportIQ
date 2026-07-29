from collections.abc import Generator
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.main import app


@pytest.fixture
def database_session() -> MagicMock:
    return MagicMock(spec=Session)


@pytest.fixture
def client(database_session: MagicMock) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield database_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_readiness_returns_ready(
    client: TestClient,
    database_session: MagicMock,
) -> None:
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    database_session.execute.assert_called_once()


def test_readiness_returns_503_when_database_is_unavailable(
    client: TestClient,
    database_session: MagicMock,
) -> None:
    database_session.execute.side_effect = OperationalError(
        "SELECT 1",
        {},
        ConnectionError("database unavailable"),
    )

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "detail": {
            "code": "database_unavailable",
            "message": "Database is not ready.",
        }
    }
