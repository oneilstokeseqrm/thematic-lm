"""Unit tests for coder agent prompt template and formatting.

Tests verify that the prompt template includes all required instructions
and that the _build_prompt method correctly formats the template.
"""

import pytest

from thematic_lm.agents.coder import CoderAgent, CODER_PROMPT_TEMPLATE
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
def coder_agent(sample_identity):
    """Create a coder agent instance for testing."""
    from unittest.mock import AsyncMock
    mock_client = AsyncMock()
    return CoderAgent(identity=sample_identity, dry_run=True, openai_client=mock_client)


def test_prompt_formatting_with_sample_chunk_text(coder_agent):
    """Test that prompt is correctly formatted with chunk text."""
    chunk_text = "This is a sample text for testing the prompt formatting."
    
    prompt = coder_agent._build_prompt(chunk_text)
    
    # Verify chunk text is included in prompt
    assert chunk_text in prompt
    
    # Verify prompt is a string
    assert isinstance(prompt, str)
    
    # Verify prompt is not empty
    assert len(prompt) > 0


def test_json_array_only_instruction_present(coder_agent):
    """Test that prompt includes JSON-array-only instruction."""
    chunk_text = "Sample text"
    
    prompt = coder_agent._build_prompt(chunk_text)
    
    # Check for JSON array instruction
    assert "JSON array" in prompt or "json array" in prompt.lower()
    
    # Check for "ONLY" emphasis
    assert "ONLY" in prompt or "only" in prompt.lower()


def test_request_for_1_3_codes_present(coder_agent):
    """Test that prompt requests 1-3 codes per chunk."""
    chunk_text = "Sample text"
    
    prompt = coder_agent._build_prompt(chunk_text)
    
    # Check for code count instruction
    assert "1-3" in prompt or "1 to 3" in prompt or "one to three" in prompt.lower()
    
    # Check for "codes" or "code" mention
    assert "code" in prompt.lower()


def test_request_for_quotes_array_present(coder_agent):
    """Test that prompt requests quotes array with 1-3 quotes per code."""
    chunk_text = "Sample text"
    
    prompt = coder_agent._build_prompt(chunk_text)
    
    # Check for quotes array instruction
    assert "quotes" in prompt.lower()
    
    # Check for quote count (1-3 quotes per code)
    assert "1-3" in prompt or "1 to 3" in prompt or "one to three" in prompt.lower()


def test_verbatim_quote_instruction_present(coder_agent):
    """Test that prompt includes verbatim quote instruction."""
    chunk_text = "Sample text"
    
    prompt = coder_agent._build_prompt(chunk_text)
    
    # Check for verbatim instruction
    assert "verbatim" in prompt.lower() or "exact" in prompt.lower()
    
    # Check for instruction about quote fields
    assert "text" in prompt.lower()
    assert "start_pos" in prompt.lower()
    assert "end_pos" in prompt.lower()


def test_prompt_template_structure():
    """Test that CODER_PROMPT_TEMPLATE has expected structure."""
    # Verify template is a string
    assert isinstance(CODER_PROMPT_TEMPLATE, str)
    
    # Verify template has placeholder for text
    assert "{text}" in CODER_PROMPT_TEMPLATE
    
    # Verify template includes key instructions
    assert "JSON array" in CODER_PROMPT_TEMPLATE or "json array" in CODER_PROMPT_TEMPLATE.lower()
    assert "quotes" in CODER_PROMPT_TEMPLATE.lower()
    assert "label" in CODER_PROMPT_TEMPLATE.lower()


def test_prompt_includes_json_format_example(coder_agent):
    """Test that prompt includes JSON format example."""
    chunk_text = "Sample text"
    
    prompt = coder_agent._build_prompt(chunk_text)
    
    # Check for JSON structure indicators
    assert "[" in prompt  # Array opening
    assert "]" in prompt  # Array closing
    assert "{" in prompt  # Object opening
    assert "}" in prompt  # Object closing
    
    # Check for field names in example
    assert "label" in prompt.lower()
    assert "quotes" in prompt.lower()
    assert "text" in prompt.lower()
    assert "start_pos" in prompt.lower()
    assert "end_pos" in prompt.lower()


def test_prompt_with_multiline_chunk_text(coder_agent):
    """Test prompt formatting with multiline chunk text."""
    chunk_text = """This is a multiline
    text chunk that spans
    multiple lines."""
    
    prompt = coder_agent._build_prompt(chunk_text)
    
    # Verify multiline text is preserved
    assert chunk_text in prompt
    
    # Verify newlines are preserved
    assert "\n" in prompt


def test_prompt_with_special_characters(coder_agent):
    """Test prompt formatting with special characters in chunk text."""
    chunk_text = 'Text with "quotes" and \'apostrophes\' and {braces} and [brackets]'
    
    prompt = coder_agent._build_prompt(chunk_text)
    
    # Verify special characters are preserved
    assert chunk_text in prompt
    assert '"' in prompt
    assert "'" in prompt


def test_prompt_with_unicode_text(coder_agent):
    """Test prompt formatting with Unicode characters."""
    chunk_text = "Text with émojis 😀 and spëcial çharacters"
    
    prompt = coder_agent._build_prompt(chunk_text)
    
    # Verify Unicode is preserved
    assert chunk_text in prompt
    assert "😀" in prompt
    assert "é" in prompt
