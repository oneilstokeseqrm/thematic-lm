"""Configuration settings for Thematic-LM."""

from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration."""

    DATABASE_URL: str = Field(..., description="PostgreSQL connection string")

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate that DATABASE_URL uses asyncpg driver."""
        if not v.startswith("postgresql+asyncpg://"):
            raise ValueError("DATABASE_URL must use postgresql+asyncpg:// driver")
        return v


class OpenAISettings(BaseSettings):
    """OpenAI API configuration."""

    OPENAI_API_KEY: str = Field(..., description="OpenAI API key")
    OPENAI_MODEL: str = Field(default="gpt-4o", description="Primary model for agents")
    OPENAI_EMBEDDING_MODEL: str = Field(
        default="text-embedding-3-large", description="Embedding model"
    )


class PineconeSettings(BaseSettings):
    """Pinecone vector storage configuration."""

    PINECONE_API_KEY: str = Field(..., description="Pinecone API key")
    PINECONE_ENVIRONMENT: str = Field(..., description="Pinecone environment")
    PINECONE_INDEX_NAME: str = Field(..., description="Pinecone index name")


class PipelineSettings(BaseSettings):
    """Pipeline execution configuration."""

    COST_BUDGET_USD: float = Field(default=5.0, description="Maximum cost per analysis")
    DRY_RUN: bool = Field(default=True, description="Simulate LLM calls without API requests")
    IDENTITIES_PATH: str = Field(default="identities.yaml", description="Path to identities file")


class Settings(BaseSettings):
    """Combined application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Sub-settings
    DATABASE_URL: str
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-large"
    PINECONE_API_KEY: str
    PINECONE_ENVIRONMENT: str
    PINECONE_INDEX_NAME: str
    COST_BUDGET_USD: float = 5.0
    DRY_RUN: bool = True
    IDENTITIES_PATH: str = "identities.yaml"
    LOG_LEVEL: str = "INFO"
    LIVE_TESTS: bool = False

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate that DATABASE_URL uses asyncpg driver."""
        if not v.startswith("postgresql+asyncpg://"):
            raise ValueError("DATABASE_URL must use postgresql+asyncpg:// driver")
        return v

    @property
    def database(self) -> DatabaseSettings:
        """Get database settings."""
        return DatabaseSettings(DATABASE_URL=self.DATABASE_URL)

    @property
    def openai(self) -> OpenAISettings:
        """Get OpenAI settings."""
        return OpenAISettings(
            OPENAI_API_KEY=self.OPENAI_API_KEY,
            OPENAI_MODEL=self.OPENAI_MODEL,
            OPENAI_EMBEDDING_MODEL=self.OPENAI_EMBEDDING_MODEL,
        )

    @property
    def pinecone(self) -> PineconeSettings:
        """Get Pinecone settings."""
        return PineconeSettings(
            PINECONE_API_KEY=self.PINECONE_API_KEY,
            PINECONE_ENVIRONMENT=self.PINECONE_ENVIRONMENT,
            PINECONE_INDEX_NAME=self.PINECONE_INDEX_NAME,
        )

    @property
    def pipeline(self) -> PipelineSettings:
        """Get pipeline settings."""
        return PipelineSettings(
            COST_BUDGET_USD=self.COST_BUDGET_USD,
            DRY_RUN=self.DRY_RUN,
            IDENTITIES_PATH=self.IDENTITIES_PATH,
        )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
