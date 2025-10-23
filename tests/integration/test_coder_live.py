"""Live integration test for coder agent with real OpenAI API.

This test is gated by LIVE_TESTS=1 and requires a valid OPENAI_API_KEY.
It validates the full coder agent workflow with real API calls.
"""

import os
import uuid
import pytest
from dotenv import load_dotenv

from src.thematic_lm.agents.coder import CoderAgent
from src.thematic_lm.utils.identities import load_identities
from src.thematic_lm.utils.quote_id import QUOTE_ID_PATTERN

# Load .env file for API keys
load_dotenv()


@pytest.mark.skipif(
    os.getenv("LIVE_TESTS") != "1",
    reason="Live tests disabled (set LIVE_TESTS=1 to enable)"
)
@pytest.mark.asyncio
async def test_coder_agent_live_integration():
    """Test coder agent with real OpenAI API call.
    
    This test validates:
    - CoderResult returned with codes and token_usage
    - Codes generated (1-3 codes)
    - Quote IDs match regex pattern
    - Offsets are valid (start < end, within chunk bounds)
    - Token usage recorded (prompt_tokens > 0, completion_tokens > 0)
    - CoderResult structure matches internal/agents-coder@v1 interface
    """
    # Verify OpenAI API key is set
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set")
    
    # Load identities
    identities = load_identities("identities.yaml")
    assert len(identities) > 0, "No identities loaded"
    
    # Use first identity for test
    identity = identities[0]
    
    # Create coder agent (not in dry_run mode)
    agent = CoderAgent(identity=identity, model="gpt-4o", dry_run=False)
    
    # Create tiny sample interaction (1-2 sentences)
    sample_text = "The customer service was excellent. The staff were friendly and helpful."
    interaction_id = str(uuid.uuid4())
    
    # Create chunk
    chunk = {
        "chunk_index": 0,
        "text": sample_text,
        "start_pos": 0,
        "end_pos": len(sample_text),
        "token_count": 15
    }
    
    # Call coder agent
    result = await agent.code_chunk(chunk, interaction_id)
    
    # Verify CoderResult structure
    assert "codes" in result, "CoderResult missing 'codes' field"
    assert "token_usage" in result, "CoderResult missing 'token_usage' field"
    
    # Verify token_usage structure
    token_usage = result["token_usage"]
    assert "prompt_tokens" in token_usage, "TokenUsage missing 'prompt_tokens'"
    assert "completion_tokens" in token_usage, "TokenUsage missing 'completion_tokens'"
    
    # Verify token usage recorded (prompt_tokens > 0, completion_tokens > 0)
    assert token_usage["prompt_tokens"] > 0, "prompt_tokens should be > 0"
    assert token_usage["completion_tokens"] > 0, "completion_tokens should be > 0"
    
    # Verify codes generated (1-3 codes)
    codes = result["codes"]
    assert isinstance(codes, list), "codes should be a list"
    assert 1 <= len(codes) <= 3, f"Expected 1-3 codes, got {len(codes)}"
    
    # Verify each code structure
    for code in codes:
        assert "label" in code, "Code missing 'label' field"
        assert "quotes" in code, "Code missing 'quotes' field"
        assert isinstance(code["label"], str), "Code label should be string"
        assert len(code["label"]) > 0, "Code label should not be empty"
        
        # Verify quotes array (1-3 quotes per code)
        quotes = code["quotes"]
        assert isinstance(quotes, list), "quotes should be a list"
        assert 1 <= len(quotes) <= 3, f"Expected 1-3 quotes per code, got {len(quotes)}"
        
        # Verify each quote structure
        for quote in quotes:
            # Verify required fields
            assert "quote_id" in quote, "Quote missing 'quote_id' field"
            assert "text" in quote, "Quote missing 'text' field"
            assert "interaction_id" in quote, "Quote missing 'interaction_id' field"
            assert "chunk_index" in quote, "Quote missing 'chunk_index' field"
            assert "start_pos" in quote, "Quote missing 'start_pos' field"
            assert "end_pos" in quote, "Quote missing 'end_pos' field"
            
            # Verify quote_id matches regex pattern
            assert QUOTE_ID_PATTERN.match(quote["quote_id"]), \
                f"Quote ID '{quote['quote_id']}' doesn't match pattern"
            
            # Verify offsets are valid (start < end, within chunk bounds)
            start_pos = quote["start_pos"]
            end_pos = quote["end_pos"]
            assert start_pos < end_pos, \
                f"start_pos ({start_pos}) should be < end_pos ({end_pos})"
            assert 0 <= start_pos < len(sample_text), \
                f"start_pos ({start_pos}) out of bounds (0-{len(sample_text)})"
            assert 0 < end_pos <= len(sample_text), \
                f"end_pos ({end_pos}) out of bounds (0-{len(sample_text)})"
            
            # Verify quote text matches chunk text at offsets
            expected_text = sample_text[start_pos:end_pos]
            assert quote["text"] == expected_text, \
                f"Quote text doesn't match chunk text at offsets: " \
                f"expected '{expected_text}', got '{quote['text']}'"
            
            # Verify interaction_id matches
            assert quote["interaction_id"] == interaction_id, \
                "Quote interaction_id doesn't match"
            
            # Verify chunk_index matches
            assert quote["chunk_index"] == 0, \
                "Quote chunk_index doesn't match"
    
    # Log success for monitoring
    print(f"\n✓ Live test passed:")
    print(f"  - Codes generated: {len(codes)}")
    print(f"  - Total quotes: {sum(len(c['quotes']) for c in codes)}")
    print(f"  - Token usage: {token_usage['prompt_tokens']} prompt + "
          f"{token_usage['completion_tokens']} completion = "
          f"{token_usage['prompt_tokens'] + token_usage['completion_tokens']} total")
