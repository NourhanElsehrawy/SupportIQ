import os
import subprocess
import sys

import pytest
from sqlalchemy import create_engine, inspect

pytestmark = pytest.mark.integration


def run_alembic(revision: str) -> None:
    environment = os.environ.copy()
    environment["DATABASE_URL"] = environment["TEST_DATABASE_URL"]
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", revision],
        check=True,
        env=environment,
    )


def test_initial_migration_is_reversible() -> None:
    database_url = os.environ["TEST_DATABASE_URL"]
    environment = os.environ.copy()
    environment["DATABASE_URL"] = database_url

    subprocess.run(
        [sys.executable, "-m", "alembic", "downgrade", "base"],
        check=True,
        env=environment,
    )

    engine = create_engine(database_url)
    try:
        assert "users" not in inspect(engine).get_table_names()

        run_alembic("head")

        assert "users" in inspect(engine).get_table_names()
    finally:
        engine.dispose()
