"""Pytest configuration and shared fixtures."""

import os
from typing import AsyncGenerator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.thematic_lm.models.database import get_db_session


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session for tests.

    Note:
        Only available when LIVE_TESTS=1
    """
    if os.getenv("LIVE_TESTS") != "1":
        pytest.skip("Live tests disabled")

    async for session in get_db_session():
        yield session


def pytest_configure(config):
    """Register custom markers for test gating."""
    config.addinivalue_line(
        "markers",
        "live: mark test as requiring live API calls (requires LIVE_TESTS=1)"
    )


# LIVE_TESTS gating marker
live_tests_marker = pytest.mark.skipif(
    os.getenv("LIVE_TESTS") != "1",
    reason="Live tests disabled (set LIVE_TESTS=1 to enable)"
)
