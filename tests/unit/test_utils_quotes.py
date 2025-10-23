"""Tests for quote validation and repair utilities."""

import pytest
from unittest.mock import patch, MagicMock

from thematic_lm.utils.quotes import normalize_quote_span


def test_valid_offsets_returns_as_is():
    """Test that valid offsets are returned unchanged."""
    chunk_text = "This is a sample text with some content."
    quote_text = "sample text"
    start_pos = 10
    end_pos = 21
    
    result = normalize_quote_span(quote_text, chunk_text, start_pos, end_pos)
    
    assert result == (10, 21)
    assert chunk_text[start_pos:end_pos] == quote_text


@patch('thematic_lm.utils.quotes.logger')
def test_invalid_offsets_but_quote_found_repairs(mock_logger):
    """Test that invalid offsets are repaired when quote is found."""
    chunk_text = "This is a sample text with some content."
    quote_text = "sample text"
    # Provide wrong offsets
    start_pos = 0
    end_pos = 5
    
    result = normalize_quote_span(quote_text, chunk_text, start_pos, end_pos)
    
    # Should find and repair to correct offsets
    assert result == (10, 21)
    assert chunk_text[result[0]:result[1]] == quote_text
    
    # Verify INFO log was emitted
    mock_logger.info.assert_called_once()
    call_args = mock_logger.info.call_args
    assert "Repaired quote offsets" in call_args[0]


@patch('thematic_lm.utils.quotes.logger')
def test_quote_not_in_chunk_returns_none(mock_logger):
    """Test that None is returned when quote is not found in chunk."""
    chunk_text = "This is a sample text with some content."
    quote_text = "missing quote"
    start_pos = 0
    end_pos = 13
    
    result = normalize_quote_span(quote_text, chunk_text, start_pos, end_pos)
    
    assert result is None
    
    # Verify WARNING log was emitted
    mock_logger.warning.assert_called_once()
    call_args = mock_logger.warning.call_args
    assert "Quote not found in chunk" in call_args[0]


def test_unicode_characters_in_quote_and_chunk():
    """Test that Unicode characters are handled correctly."""
    # Test with emoji and multi-byte characters
    chunk_text = "Hello 👋 world! This is a test with émojis 🎉 and accénts."
    quote_text = "émojis 🎉 and accénts"
    
    # Find the correct offsets
    start_pos = chunk_text.index(quote_text)
    end_pos = start_pos + len(quote_text)
    
    result = normalize_quote_span(quote_text, chunk_text, start_pos, end_pos)
    
    assert result == (start_pos, end_pos)
    assert chunk_text[result[0]:result[1]] == quote_text


def test_unicode_repair_with_wrong_offsets():
    """Test that Unicode quotes can be repaired with wrong offsets."""
    chunk_text = "Hello 👋 world! This is a test with émojis 🎉 and accénts."
    quote_text = "émojis 🎉 and accénts"
    # Provide wrong offsets
    start_pos = 0
    end_pos = 10
    
    result = normalize_quote_span(quote_text, chunk_text, start_pos, end_pos)
    
    # Should find and repair
    assert result is not None
    assert chunk_text[result[0]:result[1]] == quote_text


def test_no_offsets_provided_attempts_repair():
    """Test that when no offsets provided, it attempts to find the quote."""
    chunk_text = "This is a sample text with some content."
    quote_text = "sample text"
    
    result = normalize_quote_span(quote_text, chunk_text, None, None)
    
    assert result == (10, 21)
    assert chunk_text[result[0]:result[1]] == quote_text


def test_partial_offsets_provided_attempts_repair():
    """Test that when only one offset is provided, it attempts repair."""
    chunk_text = "This is a sample text with some content."
    quote_text = "sample text"
    
    # Only start_pos provided
    result = normalize_quote_span(quote_text, chunk_text, 10, None)
    assert result == (10, 21)
    
    # Only end_pos provided
    result = normalize_quote_span(quote_text, chunk_text, None, 21)
    assert result == (10, 21)


def test_offsets_out_of_bounds_attempts_repair():
    """Test that out-of-bounds offsets trigger repair."""
    chunk_text = "This is a sample text with some content."
    quote_text = "sample text"
    
    # start_pos negative
    result = normalize_quote_span(quote_text, chunk_text, -5, 10)
    assert result == (10, 21)
    
    # end_pos beyond chunk length
    result = normalize_quote_span(quote_text, chunk_text, 10, 1000)
    assert result == (10, 21)


def test_empty_quote_text():
    """Test handling of empty quote text."""
    chunk_text = "This is a sample text."
    quote_text = ""
    
    result = normalize_quote_span(quote_text, chunk_text, 0, 0)
    
    # Empty string is found at position 0
    assert result == (0, 0)


def test_quote_at_start_of_chunk():
    """Test quote at the beginning of chunk."""
    chunk_text = "sample text with more content"
    quote_text = "sample text"
    
    result = normalize_quote_span(quote_text, chunk_text, 0, 11)
    
    assert result == (0, 11)
    assert chunk_text[result[0]:result[1]] == quote_text


def test_quote_at_end_of_chunk():
    """Test quote at the end of chunk."""
    chunk_text = "This is a sample text"
    quote_text = "sample text"
    
    result = normalize_quote_span(quote_text, chunk_text, 10, 21)
    
    assert result == (10, 21)
    assert chunk_text[result[0]:result[1]] == quote_text
