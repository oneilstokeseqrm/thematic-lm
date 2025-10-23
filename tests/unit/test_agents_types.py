"""Unit tests for agent type definitions.

Tests the TypedDict structures used in the coder agent interface
to ensure they can be instantiated correctly and have the expected structure.
"""

from thematic_lm.agents.types import Code, CoderResult, Quote, TokenUsage


def test_quote_instantiation():
    """Test Quote TypedDict can be instantiated with all required fields."""
    quote: Quote = {
        "quote_id": "550e8400-e29b-41d4-a716-446655440000:ch_0:0-50",
        "text": "This is a sample quote from the interaction text.",
        "interaction_id": "550e8400-e29b-41d4-a716-446655440000",
        "chunk_index": 0,
        "start_pos": 0,
        "end_pos": 50
    }
    
    assert quote["quote_id"] == "550e8400-e29b-41d4-a716-446655440000:ch_0:0-50"
    assert quote["text"] == "This is a sample quote from the interaction text."
    assert quote["interaction_id"] == "550e8400-e29b-41d4-a716-446655440000"
    assert quote["chunk_index"] == 0
    assert quote["start_pos"] == 0
    assert quote["end_pos"] == 50


def test_code_instantiation():
    """Test Code TypedDict can be instantiated with quotes list."""
    quote1: Quote = {
        "quote_id": "550e8400-e29b-41d4-a716-446655440000:ch_0:0-30",
        "text": "First quote supporting the code",
        "interaction_id": "550e8400-e29b-41d4-a716-446655440000",
        "chunk_index": 0,
        "start_pos": 0,
        "end_pos": 30
    }
    
    quote2: Quote = {
        "quote_id": "550e8400-e29b-41d4-a716-446655440000:ch_0:50-85",
        "text": "Second quote supporting the code",
        "interaction_id": "550e8400-e29b-41d4-a716-446655440000",
        "chunk_index": 0,
        "start_pos": 50,
        "end_pos": 85
    }
    
    code: Code = {
        "label": "Customer Satisfaction",
        "quotes": [quote1, quote2]
    }
    
    assert code["label"] == "Customer Satisfaction"
    assert len(code["quotes"]) == 2
    assert code["quotes"][0]["text"] == "First quote supporting the code"
    assert code["quotes"][1]["text"] == "Second quote supporting the code"


def test_token_usage_instantiation():
    """Test TokenUsage TypedDict can be instantiated with token counts."""
    token_usage: TokenUsage = {
        "prompt_tokens": 150,
        "completion_tokens": 75
    }
    
    assert token_usage["prompt_tokens"] == 150
    assert token_usage["completion_tokens"] == 75


def test_coder_result_instantiation():
    """Test CoderResult TypedDict can be instantiated with codes and token_usage."""
    quote: Quote = {
        "quote_id": "550e8400-e29b-41d4-a716-446655440000:ch_0:0-40",
        "text": "Representative quote for the code",
        "interaction_id": "550e8400-e29b-41d4-a716-446655440000",
        "chunk_index": 0,
        "start_pos": 0,
        "end_pos": 40
    }
    
    code: Code = {
        "label": "Product Quality",
        "quotes": [quote]
    }
    
    token_usage: TokenUsage = {
        "prompt_tokens": 200,
        "completion_tokens": 100
    }
    
    coder_result: CoderResult = {
        "codes": [code],
        "token_usage": token_usage
    }
    
    assert len(coder_result["codes"]) == 1
    assert coder_result["codes"][0]["label"] == "Product Quality"
    assert coder_result["token_usage"]["prompt_tokens"] == 200
    assert coder_result["token_usage"]["completion_tokens"] == 100


def test_coder_result_structure():
    """Verify CoderResult structure matches internal/agents-coder@v1 interface."""
    # Create a complete CoderResult with multiple codes
    quote1: Quote = {
        "quote_id": "550e8400-e29b-41d4-a716-446655440000:ch_0:0-25",
        "text": "First supporting quote",
        "interaction_id": "550e8400-e29b-41d4-a716-446655440000",
        "chunk_index": 0,
        "start_pos": 0,
        "end_pos": 25
    }
    
    quote2: Quote = {
        "quote_id": "550e8400-e29b-41d4-a716-446655440000:ch_0:30-60",
        "text": "Second supporting quote",
        "interaction_id": "550e8400-e29b-41d4-a716-446655440000",
        "chunk_index": 0,
        "start_pos": 30,
        "end_pos": 60
    }
    
    code1: Code = {
        "label": "User Experience",
        "quotes": [quote1]
    }
    
    code2: Code = {
        "label": "Feature Request",
        "quotes": [quote2]
    }
    
    token_usage: TokenUsage = {
        "prompt_tokens": 300,
        "completion_tokens": 150
    }
    
    coder_result: CoderResult = {
        "codes": [code1, code2],
        "token_usage": token_usage
    }
    
    # Verify structure
    assert "codes" in coder_result
    assert "token_usage" in coder_result
    assert isinstance(coder_result["codes"], list)
    assert isinstance(coder_result["token_usage"], dict)
    
    # Verify codes structure
    for code in coder_result["codes"]:
        assert "label" in code
        assert "quotes" in code
        assert isinstance(code["label"], str)
        assert isinstance(code["quotes"], list)
        
        # Verify quotes structure
        for quote in code["quotes"]:
            assert "quote_id" in quote
            assert "text" in quote
            assert "interaction_id" in quote
            assert "chunk_index" in quote
            assert "start_pos" in quote
            assert "end_pos" in quote
    
    # Verify token_usage structure
    assert "prompt_tokens" in coder_result["token_usage"]
    assert "completion_tokens" in coder_result["token_usage"]
    assert isinstance(coder_result["token_usage"]["prompt_tokens"], int)
    assert isinstance(coder_result["token_usage"]["completion_tokens"], int)
