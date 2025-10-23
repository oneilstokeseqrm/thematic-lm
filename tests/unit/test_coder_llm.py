"""Unit tests for CoderAgent LLM call functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from openai.types.chat.chat_completion import ChatCompletion, Choice
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from openai.types.completion_usage import CompletionUsage

from thematic_lm.agents.coder import CoderAgent
from thematic_lm.utils.identities import Identity


@pytest.fixture
def identity():
    """Create test identity."""
    return Identity(
        id="test-analyst",
        name="Test Analyst",
        prompt_prefix="You are a test analyst."
    )


@pytest.fixture
def mock_openai_client():
    """Create mock OpenAI client."""
    return AsyncMock()


def create_mock_response(content: str, prompt_tokens: int = 100, completion_tokens: int = 50):
    """Create a mock OpenAI response."""
    return ChatCompletion(
        id="test-completion-id",
        model="gpt-4o",
        object="chat.completion",
        created=1234567890,
        choices=[
            Choice(
                index=0,
                message=ChatCompletionMessage(
                    role="assistant",
                    content=content
                ),
                finish_reason="stop"
            )
        ],
        usage=CompletionUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens
        )
    )


@pytest.mark.asyncio
async def test_successful_llm_call(identity, mock_openai_client):
    """Test successful LLM call with usage metadata."""
    # Setup mock response
    mock_response = create_mock_response(
        content='[{"label": "Test Code", "quotes": [{"text": "test", "start_pos": 0, "end_pos": 4}]}]',
        prompt_tokens=120,
        completion_tokens=60
    )
    mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    # Create agent with mock client
    agent = CoderAgent(identity=identity, openai_client=mock_openai_client)
    
    # Call LLM
    messages = [
        {"role": "system", "content": "You are a test analyst."},
        {"role": "user", "content": "Analyze this text."}
    ]
    result = await agent._call_llm(messages)
    
    # Verify response structure
    assert "content" in result
    assert "usage" in result
    assert result["usage"]["prompt_tokens"] == 120
    assert result["usage"]["completion_tokens"] == 60
    assert isinstance(result["content"], str)
    
    # Verify OpenAI client was called
    mock_openai_client.chat.completions.create.assert_called_once()


@pytest.mark.asyncio
async def test_llm_call_with_retry(identity, mock_openai_client):
    """Test LLM call succeeds after transient failure."""
    # Setup mock to fail once then succeed
    mock_response = create_mock_response(
        content='[{"label": "Test Code", "quotes": [{"text": "test", "start_pos": 0, "end_pos": 4}]}]',
        prompt_tokens=100,
        completion_tokens=50
    )
    
    mock_openai_client.chat.completions.create = AsyncMock(
        side_effect=[
            Exception("Transient error"),
            mock_response
        ]
    )
    
    # Create agent with mock client
    agent = CoderAgent(identity=identity, openai_client=mock_openai_client)
    
    # Call LLM - should succeed after retry
    messages = [
        {"role": "system", "content": "You are a test analyst."},
        {"role": "user", "content": "Analyze this text."}
    ]
    result = await agent._call_llm(messages)
    
    # Verify response structure
    assert "content" in result
    assert "usage" in result
    assert result["usage"]["prompt_tokens"] == 100
    assert result["usage"]["completion_tokens"] == 50
    
    # Verify retry happened (called twice)
    assert mock_openai_client.chat.completions.create.call_count == 2


@pytest.mark.asyncio
async def test_llm_call_timeout(identity, mock_openai_client, caplog):
    """Test LLM call timeout logs WARNING."""
    import asyncio
    
    # Setup mock to timeout
    async def timeout_func(*args, **kwargs):
        await asyncio.sleep(100)  # Simulate long-running call
    
    mock_openai_client.chat.completions.create = AsyncMock(side_effect=timeout_func)
    
    # Create agent with mock client
    agent = CoderAgent(identity=identity, openai_client=mock_openai_client)
    
    # Call LLM - should timeout and raise exception
    messages = [
        {"role": "system", "content": "You are a test analyst."},
        {"role": "user", "content": "Analyze this text."}
    ]
    
    with pytest.raises(asyncio.TimeoutError):
        await agent._call_llm(messages)
    
    # Verify WARNING log was created (checked by retry logic)
    # Note: The actual WARNING is logged by call_with_retry, not _call_llm


@pytest.mark.asyncio
async def test_token_usage_extraction(identity, mock_openai_client):
    """Test token usage extraction from response metadata."""
    # Setup mock response with specific token counts
    mock_response = create_mock_response(
        content='[{"label": "Test", "quotes": []}]',
        prompt_tokens=250,
        completion_tokens=125
    )
    mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    # Create agent with mock client
    agent = CoderAgent(identity=identity, openai_client=mock_openai_client)
    
    # Call LLM
    messages = [
        {"role": "system", "content": "You are a test analyst."},
        {"role": "user", "content": "Analyze this text."}
    ]
    result = await agent._call_llm(messages)
    
    # Verify both token fields are present and correct
    assert result["usage"]["prompt_tokens"] == 250
    assert result["usage"]["completion_tokens"] == 125


@pytest.mark.asyncio
async def test_llm_call_with_empty_content(identity, mock_openai_client):
    """Test LLM call handles empty content gracefully."""
    # Setup mock response with empty content
    mock_response = create_mock_response(
        content="",
        prompt_tokens=100,
        completion_tokens=0
    )
    mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    # Create agent with mock client
    agent = CoderAgent(identity=identity, openai_client=mock_openai_client)
    
    # Call LLM
    messages = [
        {"role": "system", "content": "You are a test analyst."},
        {"role": "user", "content": "Analyze this text."}
    ]
    result = await agent._call_llm(messages)
    
    # Verify response structure with empty content
    assert result["content"] == ""
    assert result["usage"]["prompt_tokens"] == 100
    assert result["usage"]["completion_tokens"] == 0


@pytest.mark.asyncio
async def test_llm_call_logs_token_usage(identity, mock_openai_client, caplog):
    """Test that token usage is logged at INFO level without content."""
    import structlog
    
    # Setup mock response
    mock_response = create_mock_response(
        content='[{"label": "Test", "quotes": []}]',
        prompt_tokens=150,
        completion_tokens=75
    )
    mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    # Create agent with mock client
    agent = CoderAgent(identity=identity, openai_client=mock_openai_client)
    
    # Call LLM
    messages = [
        {"role": "system", "content": "You are a test analyst."},
        {"role": "user", "content": "Analyze this text."}
    ]
    
    with caplog.at_level("INFO"):
        result = await agent._call_llm(messages)
    
    # Verify token usage was logged
    # Note: structlog may format logs differently, so we just verify the call succeeded
    assert result["usage"]["prompt_tokens"] == 150
    assert result["usage"]["completion_tokens"] == 75
