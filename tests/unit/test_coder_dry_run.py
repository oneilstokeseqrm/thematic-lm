"""Tests for CoderAgent DRY_RUN mode."""

import os
from unittest.mock import AsyncMock, patch

import pytest

from thematic_lm.agents.coder import CoderAgent
from thematic_lm.utils.identities import Identity


@pytest.fixture
def sample_identity():
    """Create a sample identity for testing."""
    return Identity(
        id="test-analyst",
        name="Test Analyst",
        prompt_prefix="You are a test analyst."
    )


@pytest.fixture
def sample_chunk():
    """Create a sample chunk for testing."""
    return {
        "chunk_index": 0,
        "text": "This is a sample text for testing purposes.",
        "start_pos": 0,
        "end_pos": 44,
        "token_count": 10
    }


@pytest.mark.asyncio
async def test_dry_run_enabled_returns_mock_result(sample_identity, sample_chunk):
    """Test that DRY_RUN=1 returns mock CoderResult without LLM call."""
    # Set DRY_RUN environment variable
    with patch.dict(os.environ, {"DRY_RUN": "1"}):
        agent = CoderAgent(identity=sample_identity)
        
        # Verify dry_run is enabled
        assert agent.dry_run is True
        
        # Call code_chunk
        result = await agent.code_chunk(
            chunk=sample_chunk,
            interaction_id="test-interaction-123"
        )
        
        # Verify result structure
        assert "codes" in result
        assert "token_usage" in result
        assert isinstance(result["codes"], list)
        assert isinstance(result["token_usage"], dict)
        
        # Verify mock token usage
        assert result["token_usage"]["prompt_tokens"] == 100
        assert result["token_usage"]["completion_tokens"] == 50
        
        # Verify mock codes
        assert len(result["codes"]) == 1
        code = result["codes"][0]
        assert "label" in code
        assert "quotes" in code
        assert len(code["quotes"]) == 1
        
        # Verify mock quote has valid quote_id
        quote = code["quotes"][0]
        assert "quote_id" in quote
        assert "test-interaction-123" in quote["quote_id"]
        assert ":ch_0:" in quote["quote_id"]


@pytest.mark.asyncio
async def test_dry_run_disabled_calls_llm(sample_identity, sample_chunk):
    """Test that DRY_RUN=0 calls real LLM (mocked in test)."""
    # Mock OpenAI client
    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock()]
    mock_response.choices[0].message.content = """[
        {
            "label": "Test Code",
            "quotes": [
                {
                    "text": "This is a sample text",
                    "start_pos": 0,
                    "end_pos": 21
                }
            ]
        }
    ]"""
    mock_response.usage = AsyncMock()
    mock_response.usage.prompt_tokens = 150
    mock_response.usage.completion_tokens = 75
    mock_response.usage.total_tokens = 225
    
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    # Set DRY_RUN=0
    with patch.dict(os.environ, {"DRY_RUN": "0"}):
        agent = CoderAgent(
            identity=sample_identity,
            openai_client=mock_client
        )
        
        # Verify dry_run is disabled
        assert agent.dry_run is False
        
        # Call code_chunk
        result = await agent.code_chunk(
            chunk=sample_chunk,
            interaction_id="test-interaction-456"
        )
        
        # Verify LLM was called
        assert mock_client.chat.completions.create.called
        
        # Verify result structure
        assert "codes" in result
        assert "token_usage" in result
        
        # Verify actual token usage from LLM
        assert result["token_usage"]["prompt_tokens"] == 150
        assert result["token_usage"]["completion_tokens"] == 75


@pytest.mark.asyncio
async def test_mock_result_has_valid_structure(sample_identity, sample_chunk):
    """Test that mock CoderResult has valid structure with codes and token_usage."""
    agent = CoderAgent(identity=sample_identity, dry_run=True)
    
    result = await agent.code_chunk(
        chunk=sample_chunk,
        interaction_id="test-interaction-789"
    )
    
    # Verify CoderResult structure
    assert isinstance(result, dict)
    assert "codes" in result
    assert "token_usage" in result
    
    # Verify codes structure
    assert isinstance(result["codes"], list)
    assert len(result["codes"]) > 0
    
    code = result["codes"][0]
    assert "label" in code
    assert "quotes" in code
    assert isinstance(code["quotes"], list)
    assert len(code["quotes"]) > 0
    
    # Verify quote structure
    quote = code["quotes"][0]
    assert "quote_id" in quote
    assert "text" in quote
    assert "interaction_id" in quote
    assert "chunk_index" in quote
    assert "start_pos" in quote
    assert "end_pos" in quote
    
    # Verify token_usage structure
    assert isinstance(result["token_usage"], dict)
    assert "prompt_tokens" in result["token_usage"]
    assert "completion_tokens" in result["token_usage"]


@pytest.mark.asyncio
async def test_mock_token_usage_values(sample_identity, sample_chunk):
    """Test that mock token_usage contains prompt_tokens=100 and completion_tokens=50."""
    agent = CoderAgent(identity=sample_identity, dry_run=True)
    
    result = await agent.code_chunk(
        chunk=sample_chunk,
        interaction_id="test-interaction-999"
    )
    
    # Verify exact mock token usage values
    assert result["token_usage"]["prompt_tokens"] == 100
    assert result["token_usage"]["completion_tokens"] == 50


@pytest.mark.asyncio
async def test_mock_codes_have_valid_quote_id(sample_identity, sample_chunk):
    """Test that mock codes have valid quote_id."""
    agent = CoderAgent(identity=sample_identity, dry_run=True)
    
    interaction_id = "550e8400-e29b-41d4-a716-446655440000"
    result = await agent.code_chunk(
        chunk=sample_chunk,
        interaction_id=interaction_id
    )
    
    # Verify quote_id format
    quote = result["codes"][0]["quotes"][0]
    quote_id = quote["quote_id"]
    
    # Quote ID should match pattern: {interaction_id}:ch_{chunk_index}:{start_pos}-{end_pos}
    assert interaction_id in quote_id
    assert ":ch_0:" in quote_id  # chunk_index is 0
    assert quote_id.endswith(":0-20")  # start_pos=0, end_pos=20
    
    # Verify quote_id components match quote fields
    assert quote["interaction_id"] == interaction_id
    assert quote["chunk_index"] == 0
    assert quote["start_pos"] == 0
    assert quote["end_pos"] == 20


@pytest.mark.asyncio
async def test_constructor_param_overrides_env_var(sample_identity, sample_chunk):
    """Test that constructor dry_run parameter overrides DRY_RUN env var."""
    # Set DRY_RUN=0 in environment
    with patch.dict(os.environ, {"DRY_RUN": "0"}):
        # But pass dry_run=True to constructor
        agent = CoderAgent(identity=sample_identity, dry_run=True)
        
        # Verify dry_run is enabled (constructor param wins)
        assert agent.dry_run is True
        
        # Verify it returns mock result
        result = await agent.code_chunk(
            chunk=sample_chunk,
            interaction_id="test-interaction-override"
        )
        
        assert result["token_usage"]["prompt_tokens"] == 100
        assert result["token_usage"]["completion_tokens"] == 50
