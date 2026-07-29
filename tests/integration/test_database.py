import os
import uuid

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.models import User

pytestmark = pytest.mark.integration


def test_user_can_be_persisted_and_loaded() -> None:
    database_url = os.environ["TEST_DATABASE_URL"]
    engine = create_engine(database_url)
    email = f"integration-{uuid.uuid4()}@example.com"

    try:
        with Session(engine) as session:
            user = User(email=email)
            session.add(user)
            session.commit()
            user_id = user.id

        with Session(engine) as session:
            persisted_user = session.scalar(select(User).where(User.id == user_id))
            assert persisted_user is not None
            assert persisted_user.email == email

            session.delete(persisted_user)
            session.commit()
    finally:
        engine.dispose()
