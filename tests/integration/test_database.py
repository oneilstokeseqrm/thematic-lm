"""Integration tests for database operations."""

import os
import uuid
from datetime import datetime
from decimal import Decimal

import pytest
from sqlalchemy import select

from src.thematic_lm.models.database import Analysis, AnalysisStatus, get_db_session, get_engine


@pytest.mark.skipif(
    os.getenv("LIVE_TESTS") != "1",
    reason="Live tests disabled (set LIVE_TESTS=1 to enable)",
)
@pytest.mark.asyncio
async def test_database_connection() -> None:
    """Test async database connection."""
    engine = get_engine()
    async with engine.connect() as conn:
        result = await conn.execute(select(1))
        assert result.scalar() == 1


@pytest.mark.skipif(
    os.getenv("LIVE_TESTS") != "1",
    reason="Live tests disabled (set LIVE_TESTS=1 to enable)",
)
@pytest.mark.asyncio
async def test_create_analysis_record() -> None:
    """Test creating an Analysis record."""
    analysis_id = uuid.uuid4()
    account_id = uuid.uuid4()
    tenant_id = uuid.uuid4()

    async for session in get_db_session():
        try:
            # Create analysis
            analysis = Analysis(
                id=analysis_id,
                account_id=account_id,
                tenant_id=tenant_id,
                status=AnalysisStatus.PENDING,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 31),
                estimated_cost_usd=Decimal("2.50"),
            )

            session.add(analysis)
            await session.commit()
            await session.refresh(analysis)

            # Verify creation
            assert analysis.id == analysis_id
            assert analysis.status == AnalysisStatus.PENDING
            assert analysis.estimated_cost_usd == Decimal("2.50")

        finally:
            # Cleanup
            await session.execute(
                select(Analysis).where(Analysis.id == analysis_id)
            )
            result = await session.execute(
                select(Analysis).where(Analysis.id == analysis_id)
            )
            if result.scalar_one_or_none():
                await session.delete(analysis)
                await session.commit()


@pytest.mark.skipif(
    os.getenv("LIVE_TESTS") != "1",
    reason="Live tests disabled (set LIVE_TESTS=1 to enable)",
)
@pytest.mark.asyncio
async def test_query_analysis_by_id() -> None:
    """Test querying Analysis by ID."""
    analysis_id = uuid.uuid4()
    account_id = uuid.uuid4()
    tenant_id = uuid.uuid4()

    async for session in get_db_session():
        try:
            # Create analysis
            analysis = Analysis(
                id=analysis_id,
                account_id=account_id,
                tenant_id=tenant_id,
                status=AnalysisStatus.PENDING,
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 1, 31),
                estimated_cost_usd=Decimal("2.50"),
            )

            session.add(analysis)
            await session.commit()

            # Query by ID
            stmt = select(Analysis).where(Analysis.id == analysis_id)
            result = await session.execute(stmt)
            found_analysis = result.scalar_one_or_none()

            assert found_analysis is not None
            assert found_analysis.id == analysis_id
            assert found_analysis.account_id == account_id

        finally:
            # Cleanup
            stmt = select(Analysis).where(Analysis.id == analysis_id)
            result = await session.execute(stmt)
            found = result.scalar_one_or_none()
            if found:
                await session.delete(found)
                await session.commit()
