from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.db import session as session_module


def test_get_db_closes_session(monkeypatch: pytest.MonkeyPatch) -> None:
    session = MagicMock(spec=Session)
    monkeypatch.setattr(session_module, "SessionFactory", MagicMock(return_value=session))

    dependency = session_module.get_db()
    assert next(dependency) is session

    with pytest.raises(StopIteration):
        next(dependency)

    session.close.assert_called_once_with()


def test_get_db_rolls_back_and_closes_after_error(monkeypatch: pytest.MonkeyPatch) -> None:
    session = MagicMock(spec=Session)
    monkeypatch.setattr(session_module, "SessionFactory", MagicMock(return_value=session))

    dependency = session_module.get_db()
    next(dependency)

    with pytest.raises(RuntimeError, match="request failed"):
        dependency.throw(RuntimeError("request failed"))

    session.rollback.assert_called_once_with()
    session.close.assert_called_once_with()
