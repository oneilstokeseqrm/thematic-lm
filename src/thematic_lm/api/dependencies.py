"""FastAPI dependencies."""

from typing import AsyncGenerator, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings, get_settings
from ..models.database import get_db_session

security = HTTPBearer()


def get_settings_dependency() -> Settings:
    """Get application settings.

    Returns:
        Application settings
    """
    return get_settings()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session.

    Yields:
        AsyncSession for database operations
    """
    async for session in get_db_session():
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, str]:
    """Get current authenticated user (placeholder).

    Args:
        credentials: Bearer token credentials

    Returns:
        Mock user dictionary

    Raises:
        HTTPException: If authentication fails

    Note:
        This is a placeholder implementation for Phase A.
        TODO: Phase B - Implement proper JWT validation and user extraction.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
        )

    # Placeholder: Accept any bearer token
    # TODO: Phase B - Validate JWT and extract user/tenant info
    return {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "tenant_id": "660e8400-e29b-41d4-a716-446655440001",
        "account_id": "770e8400-e29b-41d4-a716-446655440002",
    }
