import os

import pytest


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    if os.getenv("TEST_DATABASE_URL"):
        return

    skip_integration = pytest.mark.skip(reason="TEST_DATABASE_URL is not configured")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)
