"""Integration tests for CoderAgent.code_chunk method.

Tests the full integration of JSON parsing, quote validation, and quote_id encoding.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
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
def sample_chunk():
    """Create sample chunk for testing."""
    return {
        "chunk_index": 0,
        "text": "This is a test sentence. This is another test sentence with more content.",
        "start_pos": 0,
        "end_pos": 73,
        "token_count": 15
    }


@pytest.fixture
def mock_openai_client():
    """Create mock OpenAI client."""
    client = MagicMock()
    client.chat = MagicMock()
    client.chat.completions = MagicMock()
    return client


@pytest.mark.asyncio
async def test_valid_llm_response_with_quotes_array(identity, sample_chunk, mock_openai_client):
    """Test valid LLM response with quotes array - all quotes valid."""
    # Mock response with valid quotes
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = """[
        {
            "label": "Test Theme",
            "quotes": [
                {
                    "text": "This is a test sentence.",
                    "start_pos": 0,
                    "end_pos": 24
                }
            ]
        }
    ]"""
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 150
    mock_response.usage.completion_tokens = 75
    mock_response.usage.total_tokens = 225
    
    mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    agent = CoderAgent(identity=identity, openai_client=mock_openai_client)
    result = await agent.code_chunk(sample_chunk, "test-interaction-id")
    
    # Verify CoderResult structure
    assert "codes" in result
    assert "token_usage" in result
    assert isinstance(result["codes"], list)
    assert isinstance(result["token_usage"], dict)
    
    # Verify token usage
    assert result["token_usage"]["prompt_tokens"] == 150
    assert result["token_usage"]["completion_tokens"] == 75
    
    # Verify codes
    assert len(result["codes"]) == 1
    code = result["codes"][0]
    assert code["label"] == "Test Theme"
    assert len(code["quotes"]) == 1
    
    # Verify quote structure
    quote = code["quotes"][0]
    assert quote["text"] == "This is a test sentence."
    assert quote["interaction_id"] == "test-interaction-id"
    assert quote["chunk_index"] == 0
    assert quote["start_pos"] == 0
    assert quote["end_pos"] == 24
    assert "quote_id" in quote
    
    # Verify exact offset: chunk["text"][start:end] == quote["text"]
    assert sample_chunk["text"][quote["start_pos"]:quote["end_pos"]] == quote["text"]


@pytest.mark.asyncio
async def test_invalid_quote_offsets_should_repair(identity, sample_chunk, mock_openai_client):
    """Test invalid quote offsets - should repair using text search."""
    # Mock response with invalid offsets but valid text
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = """[
        {
            "label": "Test Theme",
            "quotes": [
                {
                    "text": "This is a test sentence.",
                    "start_pos": 100,
                    "end_pos": 200
                }
            ]
        }
    ]"""
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 150
    mock_response.usage.completion_tokens = 75
    mock_response.usage.total_tokens = 225
    
    mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    agent = CoderAgent(identity=identity, openai_client=mock_openai_client)
    result = await agent.code_chunk(sample_chunk, "test-interaction-id")
    
    # Should repair and find correct offsets
    assert len(result["codes"]) == 1
    quote = result["codes"][0]["quotes"][0]
    assert quote["text"] == "This is a test sentence."
    assert quote["start_pos"] == 0
    assert quote["end_pos"] == 24
    
    # Verify repaired offsets are correct
    assert sample_chunk["text"][quote["start_pos"]:quote["end_pos"]] == quote["text"]


@pytest.mark.asyncio
async def test_quote_not_found_should_drop_and_log_warning(identity, sample_chunk, mock_openai_client):
    """Test quote not found in chunk - should drop quote and log WARNING."""
    # Mock response with quote text not in chunk
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = """[
        {
            "label": "Test Theme",
            "quotes": [
                {
                    "text": "This text does not exist in the chunk.",
                    "start_pos": 0,
                    "end_pos": 39
                }
            ]
        }
    ]"""
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 150
    mock_response.usage.completion_tokens = 75
    mock_response.usage.total_tokens = 225
    
    mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    agent = CoderAgent(identity=identity, openai_client=mock_openai_client)
    result = await agent.code_chunk(sample_chunk, "test-interaction-id")
    
    # Should drop the invalid quote and the code (since no valid quotes remain)
    assert len(result["codes"]) == 0  # Code dropped because no valid quotes
    assert result["token_usage"]["prompt_tokens"] == 150
    assert result["token_usage"]["completion_tokens"] == 75


@pytest.mark.asyncio
async def test_code_with_no_valid_quotes_should_drop_and_log_warning(identity, sample_chunk, mock_openai_client):
    """Test code with no valid quotes - should drop code and log WARNING."""
    # Mock response with all invalid quotes
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = """[
        {
            "label": "Test Theme",
            "quotes": [
                {
                    "text": "Invalid quote 1",
                    "start_pos": 0,
                    "end_pos": 15
                },
                {
                    "text": "Invalid quote 2",
                    "start_pos": 0,
                    "end_pos": 15
                }
            ]
        }
    ]"""
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 150
    mock_response.usage.completion_tokens = 75
    mock_response.usage.total_tokens = 225
    
    mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    agent = CoderAgent(identity=identity, openai_client=mock_openai_client)
    result = await agent.code_chunk(sample_chunk, "test-interaction-id")
    
    # Should drop the code (no valid quotes)
    assert len(result["codes"]) == 0
    assert result["token_usage"]["prompt_tokens"] == 150
    assert result["token_usage"]["completion_tokens"] == 75


@pytest.mark.asyncio
async def test_more_than_3_codes_should_enforce_limit(identity, sample_chunk, mock_openai_client):
    """Test more than 3 codes - should enforce max 3 codes limit."""
    # Mock response with 5 codes
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = """[
        {
            "label": "Code 1",
            "quotes": [{"text": "This is a test sentence.", "start_pos": 0, "end_pos": 24}]
        },
        {
            "label": "Code 2",
            "quotes": [{"text": "This is another test sentence", "start_pos": 25, "end_pos": 54}]
        },
        {
            "label": "Code 3",
            "quotes": [{"text": "test sentence", "start_pos": 11, "end_pos": 24}]
        },
        {
            "label": "Code 4",
            "quotes": [{"text": "another test", "start_pos": 33, "end_pos": 45}]
        },
        {
            "label": "Code 5",
            "quotes": [{"text": "more content", "start_pos": 60, "end_pos": 72}]
        }
    ]"""
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 150
    mock_response.usage.completion_tokens = 75
    mock_response.usage.total_tokens = 225
    
    mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    agent = CoderAgent(identity=identity, openai_client=mock_openai_client)
    result = await agent.code_chunk(sample_chunk, "test-interaction-id")
    
    # Should only return first 3 codes
    assert len(result["codes"]) == 3
    assert result["codes"][0]["label"] == "Code 1"
    assert result["codes"][1]["label"] == "Code 2"
    assert result["codes"][2]["label"] == "Code 3"


@pytest.mark.asyncio
async def test_more_than_3_quotes_per_code_should_enforce_limit(identity, sample_chunk, mock_openai_client):
    """Test more than 3 quotes per code - should enforce max 3 quotes limit."""
    # Mock response with 5 quotes in one code
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = """[
        {
            "label": "Test Theme",
            "quotes": [
                {"text": "This is a test sentence.", "start_pos": 0, "end_pos": 24},
                {"text": "test sentence", "start_pos": 11, "end_pos": 24},
                {"text": "another test sentence", "start_pos": 33, "end_pos": 54},
                {"text": "test", "start_pos": 11, "end_pos": 15},
                {"text": "content", "start_pos": 66, "end_pos": 73}
            ]
        }
    ]"""
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 150
    mock_response.usage.completion_tokens = 75
    mock_response.usage.total_tokens = 225
    
    mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    agent = CoderAgent(identity=identity, openai_client=mock_openai_client)
    result = await agent.code_chunk(sample_chunk, "test-interaction-id")
    
    # Should only return first 3 quotes
    assert len(result["codes"]) == 1
    assert len(result["codes"][0]["quotes"]) == 3


@pytest.mark.asyncio
async def test_malformed_json_should_return_empty_codes_with_token_usage(identity, sample_chunk, mock_openai_client):
    """Test malformed JSON - should return CoderResult with empty codes list and token_usage."""
    # Mock response with malformed JSON
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "This is not valid JSON at all { broken"
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 150
    mock_response.usage.completion_tokens = 75
    mock_response.usage.total_tokens = 225
    
    mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    agent = CoderAgent(identity=identity, openai_client=mock_openai_client)
    result = await agent.code_chunk(sample_chunk, "test-interaction-id")
    
    # Should return empty codes but valid token_usage
    assert result["codes"] == []
    assert result["token_usage"]["prompt_tokens"] == 150
    assert result["token_usage"]["completion_tokens"] == 75


@pytest.mark.asyncio
async def test_verify_exact_offsets_for_all_quotes(identity, sample_chunk, mock_openai_client):
    """Verify chunk['text'][start:end] == quote['text'] for all quotes."""
    # Mock response with multiple valid quotes
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = """[
        {
            "label": "Theme 1",
            "quotes": [
                {"text": "This is a test sentence.", "start_pos": 0, "end_pos": 24},
                {"text": "test sentence", "start_pos": 11, "end_pos": 24}
            ]
        },
        {
            "label": "Theme 2",
            "quotes": [
                {"text": "another test sentence", "start_pos": 33, "end_pos": 54},
                {"text": "more content", "start_pos": 60, "end_pos": 72}
            ]
        }
    ]"""
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 150
    mock_response.usage.completion_tokens = 75
    mock_response.usage.total_tokens = 225
    
    mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    agent = CoderAgent(identity=identity, openai_client=mock_openai_client)
    result = await agent.code_chunk(sample_chunk, "test-interaction-id")
    
    # Verify all quotes have exact offsets
    for code in result["codes"]:
        for quote in code["quotes"]:
            extracted = sample_chunk["text"][quote["start_pos"]:quote["end_pos"]]
            assert extracted == quote["text"], (
                f"Offset mismatch: extracted '{extracted}' != quote '{quote['text']}'"
            )


@pytest.mark.asyncio
async def test_coder_result_structure_matches_contract(identity, sample_chunk, mock_openai_client):
    """Verify CoderResult structure matches internal/agents-coder@v1 interface."""
    # Mock response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = """[
        {
            "label": "Test Theme",
            "quotes": [
                {"text": "This is a test sentence.", "start_pos": 0, "end_pos": 24}
            ]
        }
    ]"""
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 150
    mock_response.usage.completion_tokens = 75
    mock_response.usage.total_tokens = 225
    
    mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    agent = CoderAgent(identity=identity, openai_client=mock_openai_client)
    result = await agent.code_chunk(sample_chunk, "test-interaction-id")
    
    # Verify top-level structure
    assert "codes" in result
    assert "token_usage" in result
    assert isinstance(result["codes"], list)
    assert isinstance(result["token_usage"], dict)
    
    # Verify token_usage structure
    assert "prompt_tokens" in result["token_usage"]
    assert "completion_tokens" in result["token_usage"]
    assert isinstance(result["token_usage"]["prompt_tokens"], int)
    assert isinstance(result["token_usage"]["completion_tokens"], int)
    
    # Verify code structure
    if result["codes"]:
        code = result["codes"][0]
        assert "label" in code
        assert "quotes" in code
        assert isinstance(code["label"], str)
        assert isinstance(code["quotes"], list)
        
        # Verify quote structure
        if code["quotes"]:
            quote = code["quotes"][0]
            assert "quote_id" in quote
            assert "text" in quote
            assert "interaction_id" in quote
            assert "chunk_index" in quote
            assert "start_pos" in quote
            assert "end_pos" in quote
            assert isinstance(quote["quote_id"], str)
            assert isinstance(quote["text"], str)
            assert isinstance(quote["interaction_id"], str)
            assert isinstance(quote["chunk_index"], int)
            assert isinstance(quote["start_pos"], int)
            assert isinstance(quote["end_pos"], int)
