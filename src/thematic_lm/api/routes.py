"""API routes for Thematic-LM BFF."""

import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import Settings
from ..models.database import Analysis, AnalysisStatus
from ..utils import get_logger

from .dependencies import get_current_user, get_db, get_settings_dependency

logger = get_logger(__name__)
router = APIRouter()


class AnalysisRequest(BaseModel):
    """Request to create a new analysis."""

    account_id: uuid.UUID = Field(..., description="Account identifier")
    start_date: date = Field(..., description="Start date for analysis")
    end_date: date = Field(..., description="End date for analysis")
    idempotency_key: Optional[str] = Field(None, description="Idempotency key for duplicate prevention")


class AnalysisResponse(BaseModel):
    """Response for analysis creation."""

    analysis_id: uuid.UUID = Field(..., description="Analysis job identifier")
    status: AnalysisStatus = Field(..., description="Current status")
    estimated_cost_usd: float = Field(..., description="Estimated cost in USD")
    created_at: datetime = Field(..., description="Creation timestamp")


class AnalysisStatusResponse(BaseModel):
    """Response for analysis status polling."""

    analysis_id: uuid.UUID = Field(..., description="Analysis job identifier")
    status: AnalysisStatus = Field(..., description="Current status")
    created_at: datetime = Field(..., description="Creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    failed_at: Optional[datetime] = Field(None, description="Failure timestamp")
    error: Optional[Dict[str, str]] = Field(None, description="Error details if failed")


@router.post("/analyze", response_model=AnalysisResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_analysis(
    request: Request,
    analysis_request: AnalysisRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings_dependency),
    current_user: Dict[str, str] = Depends(get_current_user),
) -> AnalysisResponse:
    """Submit a new analysis request.

    Args:
        request: FastAPI request object
        analysis_request: Analysis request parameters
        db: Database session
        settings: Application settings
        current_user: Authenticated user info

    Returns:
        Analysis response with job ID and estimated cost

    Raises:
        HTTPException: If validation fails or cost exceeds budget
    """
    request_id = getattr(request.state, "request_id", "unknown")

    # Validate date range
    if analysis_request.end_date < analysis_request.start_date:
        logger.warning(
            "Invalid date range",
            request_id=request_id,
            start_date=str(analysis_request.start_date),
            end_date=str(analysis_request.end_date),
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_DATE_RANGE",
                    "message": "end_date must be greater than or equal to start_date",
                }
            },
        )

    # Check idempotency
    if analysis_request.idempotency_key:
        # Look for existing analysis with same idempotency key within 24 hours
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        stmt = select(Analysis).where(
            Analysis.account_id == analysis_request.account_id,
            Analysis.idempotency_key == analysis_request.idempotency_key,
            Analysis.created_at >= cutoff_time,
        )
        result = await db.execute(stmt)
        existing_analysis = result.scalar_one_or_none()

        if existing_analysis:
            logger.info(
                "Returning existing analysis for idempotency key",
                request_id=request_id,
                analysis_id=str(existing_analysis.id),
                idempotency_key=analysis_request.idempotency_key,
            )
            return AnalysisResponse(
                analysis_id=existing_analysis.id,
                status=existing_analysis.status,
                estimated_cost_usd=float(existing_analysis.estimated_cost_usd),
                created_at=existing_analysis.created_at,
            )

    # Estimate cost (placeholder: fixed $2.50)
    # TODO: Phase B - Implement proper cost estimation based on interaction count
    estimated_cost = Decimal("2.50")

    # Validate cost against budget
    if estimated_cost > Decimal(str(settings.COST_BUDGET_USD)):
        logger.warning(
            "Cost limit exceeded",
            request_id=request_id,
            estimated_cost=float(estimated_cost),
            budget=settings.COST_BUDGET_USD,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "COST_LIMIT_EXCEEDED",
                    "message": f"Estimated cost (${estimated_cost}) exceeds budget limit (${settings.COST_BUDGET_USD})",
                    "detail": "Reduce the date range or increase COST_BUDGET_USD",
                }
            },
        )

    # Create analysis record
    analysis = Analysis(
        id=uuid.uuid4(),
        account_id=analysis_request.account_id,
        tenant_id=uuid.UUID(current_user["tenant_id"]),
        status=AnalysisStatus.PENDING,
        start_date=datetime.combine(analysis_request.start_date, datetime.min.time()),
        end_date=datetime.combine(analysis_request.end_date, datetime.max.time()),
        estimated_cost_usd=estimated_cost,
        idempotency_key=analysis_request.idempotency_key,
    )

    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)

    logger.info(
        "Analysis created",
        request_id=request_id,
        analysis_id=str(analysis.id),
        account_id=str(analysis.account_id),
        estimated_cost=float(estimated_cost),
    )

    # TODO: Phase B - Trigger orchestrator to start pipeline

    return AnalysisResponse(
        analysis_id=analysis.id,
        status=analysis.status,
        estimated_cost_usd=float(analysis.estimated_cost_usd),
        created_at=analysis.created_at,
    )


@router.get("/analysis/{analysis_id}", response_model=AnalysisStatusResponse)
async def get_analysis_status(
    request: Request,
    analysis_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: Dict[str, str] = Depends(get_current_user),
) -> AnalysisStatusResponse:
    """Get analysis status.

    Args:
        request: FastAPI request object
        analysis_id: Analysis job identifier
        db: Database session
        current_user: Authenticated user info

    Returns:
        Analysis status response

    Raises:
        HTTPException: If analysis not found
    """
    request_id = getattr(request.state, "request_id", "unknown")

    # Query analysis
    stmt = select(Analysis).where(Analysis.id == analysis_id)
    result = await db.execute(stmt)
    analysis = result.scalar_one_or_none()

    if not analysis:
        logger.warning(
            "Analysis not found",
            request_id=request_id,
            analysis_id=str(analysis_id),
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "NOT_FOUND",
                    "message": f"Analysis {analysis_id} not found",
                }
            },
        )

    logger.info(
        "Analysis status retrieved",
        request_id=request_id,
        analysis_id=str(analysis_id),
        status=analysis.status.value,
    )

    # Build response based on status
    response = AnalysisStatusResponse(
        analysis_id=analysis.id,
        status=analysis.status,
        created_at=analysis.created_at,
    )

    # TODO: Phase B - Add started_at, completed_at, failed_at timestamps
    # TODO: Phase B - Add error details for failed status
    # TODO: Phase B - Add results for completed status

    return response
