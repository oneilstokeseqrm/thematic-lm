"""Middleware for FastAPI application."""

import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from ..utils import get_logger

logger = get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID to all requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and add request ID.

        Args:
            request: Incoming request
            call_next: Next middleware or route handler

        Returns:
            Response with X-Request-Id header
        """
        # Check for existing request ID in header
        request_id = request.headers.get("X-Request-Id")
        if not request_id:
            request_id = str(uuid.uuid4())

        # Store in request state for access in routes
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add request ID to response headers
        response.headers["X-Request-Id"] = request_id

        # Log request
        logger.info(
            "Request processed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
        )

        return response
