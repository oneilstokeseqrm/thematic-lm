"""Unit tests for configuration module."""

import os
from unittest.mock import patch

import pytest

from src.thematic_lm.config import Settings


def test_settings_loads_from_env() -> None:
    """Test that settings load from environment variables."""
    env_vars = {
        "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost/testdb",
        "OPENAI_API_KEY": "sk-test-key",
        "PINECONE_API_KEY": "test-pinecone-key",
        "PINECONE_ENVIRONMENT": "test-env",
        "PINECONE_INDEX_NAME": "test-index",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        settings = Settings()
        assert settings.DATABASE_URL == env_vars["DATABASE_URL"]
        assert settings.OPENAI_API_KEY == env_vars["OPENAI_API_KEY"]
        assert settings.PINECONE_API_KEY == env_vars["PINECONE_API_KEY"]


def test_database_url_validation_fails_without_asyncpg() -> None:
    """Test that DATABASE_URL validation fails without asyncpg driver."""
    env_vars = {
        "DATABASE_URL": "postgresql://user:pass@localhost/testdb",  # Missing +asyncpg
        "OPENAI_API_KEY": "sk-test-key",
        "PINECONE_API_KEY": "test-pinecone-key",
        "PINECONE_ENVIRONMENT": "test-env",
        "PINECONE_INDEX_NAME": "test-index",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        with pytest.raises(ValueError, match="must use postgresql\\+asyncpg://"):
            Settings()


def test_settings_default_values() -> None:
    """Test that settings have correct default values."""
    env_vars = {
        "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost/testdb",
        "OPENAI_API_KEY": "sk-test-key",
        "PINECONE_API_KEY": "test-pinecone-key",
        "PINECONE_ENVIRONMENT": "test-env",
        "PINECONE_INDEX_NAME": "test-index",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        settings = Settings()
        assert settings.COST_BUDGET_USD == 5.0
        assert settings.DRY_RUN is True
        assert settings.IDENTITIES_PATH == "identities.yaml"
        assert settings.LOG_LEVEL == "INFO"
        assert settings.LIVE_TESTS is False


def test_settings_sub_properties() -> None:
    """Test that settings sub-properties work correctly."""
    env_vars = {
        "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost/testdb",
        "OPENAI_API_KEY": "sk-test-key",
        "PINECONE_API_KEY": "test-pinecone-key",
        "PINECONE_ENVIRONMENT": "test-env",
        "PINECONE_INDEX_NAME": "test-index",
    }

    with patch.dict(os.environ, env_vars, clear=True):
        settings = Settings()

        # Test database property
        db_settings = settings.database
        assert db_settings.DATABASE_URL == env_vars["DATABASE_URL"]

        # Test openai property
        openai_settings = settings.openai
        assert openai_settings.OPENAI_API_KEY == env_vars["OPENAI_API_KEY"]
        assert openai_settings.OPENAI_MODEL == "gpt-4o"

        # Test pinecone property
        pinecone_settings = settings.pinecone
        assert pinecone_settings.PINECONE_API_KEY == env_vars["PINECONE_API_KEY"]

        # Test pipeline property
        pipeline_settings = settings.pipeline
        assert pipeline_settings.COST_BUDGET_USD == 5.0
