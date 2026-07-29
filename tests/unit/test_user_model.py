from sqlalchemy import String

from app.db.base import Base
from app.models import User


def test_user_model_is_registered_with_expected_columns() -> None:
    table = Base.metadata.tables["users"]

    assert User.__tablename__ == "users"
    assert set(table.columns.keys()) == {"id", "email", "created_at"}
    assert table.primary_key.columns.keys() == ["id"]
    assert table.columns.email.unique is True
    assert isinstance(table.columns.email.type, String)
    assert table.columns.email.type.length == 320
