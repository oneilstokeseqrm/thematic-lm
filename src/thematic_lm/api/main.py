"""FastAPI application for Thematic-LM BFF."""

import os
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Dict, List

import yaml
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ..config import get_settings
from ..utils import get_logger, setup_logging

from .middleware import RequestIDMiddleware
from .routes import router

logger = get_logger(__name__)


def load_identities(identities_path: str) -> List[Dict[str, Any]]:
    """Load and validate identities from YAML file.

    Args:
        identities_path: Path to identities YAML file

    Returns:
        List of identity configurations

    Raises:
        FileNotFoundError: If identities file not found
        ValueError: If identities file is invalid
    """
    if not os.path.exists(identities_path):
        raise FileNotFoundError(f"Identities file not found: {identities_path}")

    with open(identities_path, "r") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict) or "identities" not in data:
        raise ValueError("Identities file must contain 'identities' key")

    identities = data["identities"]
    if not isinstance(identities, list):
        raise ValueError("'identities' must be a list")

    # Validate each identity
    for idx, identity in enumerate(identities):
        if not isinstance(identity, dict):
            raise ValueError(f"Identity at index {idx} must be a dictionary")

        required_fields = ["id", "name", "prompt_prefix"]
        for field in required_fields:
            if field not in identity:
                raise ValueError(f"Identity at index {idx} missing required field: {field}")

    logger.info("Loaded identities", count=len(identities))
    return identities


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager.

    Args:
        app: FastAPI application

    Yields:
        None
    """
    # Startup
    settings = get_settings()
    setup_logging(log_level=settings.LOG_LEVEL, development=True)

    logger.info("Starting Thematic-LM API")

    # Load identities
    try:
        identities = load_identities(settings.IDENTITIES_PATH)
        app.state.identities = identities
        logger.info("Identities loaded successfully", count=len(identities))
    except Exception as e:
        logger.error("Failed to load identities", error=str(e))
        raise

    yield

    # Shutdown
    logger.info("Shutting down Thematic-LM API")


# Create FastAPI app
app = FastAPI(
    title="Thematic-LM API",
    description="Multi-agent LLM system for automated thematic analysis",
    version="0.1.0",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(RequestIDMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint.

    Returns:
        Health status
    """
    return {"status": "healthy"}
