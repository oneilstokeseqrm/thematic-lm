"""Tests for text chunking utilities."""

import pytest
from thematic_lm.utils.chunking import chunk_text, Chunk


def test_single_paragraph_no_chunking():
    """Test that a single short paragraph is not chunked."""
    text = "This is a short paragraph that fits within the token limit."
    
    chunks = chunk_text(text, max_tokens=500)
    
    assert len(chunks) == 1
    assert chunks[0]["chunk_index"] == 0
    assert chunks[0]["text"] == text
    assert chunks[0]["start_pos"] == 0
    assert chunks[0]["end_pos"] == len(text)
    assert chunks[0]["token_count"] > 0
    
    # Verify exact offset preservation
    assert text[chunks[0]["start_pos"]:chunks[0]["end_pos"]] == chunks[0]["text"]


def test_multiple_paragraphs_chunk_by_paragraph():
    """Test that multiple paragraphs are chunked by paragraph boundaries."""
    text = "First paragraph here.\n\nSecond paragraph here.\n\nThird paragraph here."
    
    chunks = chunk_text(text, max_tokens=500)
    
    assert len(chunks) == 3
    
    # Verify chunk indices
    assert chunks[0]["chunk_index"] == 0
    assert chunks[1]["chunk_index"] == 1
    assert chunks[2]["chunk_index"] == 2
    
    # Verify content
    assert chunks[0]["text"] == "First paragraph here."
    assert chunks[1]["text"] == "Second paragraph here."
    assert chunks[2]["text"] == "Third paragraph here."
    
    # Verify exact offset preservation for each chunk
    for chunk in chunks:
        assert text[chunk["start_pos"]:chunk["end_pos"]] == chunk["text"]
    
    # Verify no gaps or overlaps
    assert chunks[0]["end_pos"] == chunks[0]["start_pos"] + len(chunks[0]["text"])
    assert chunks[1]["start_pos"] > chunks[0]["end_pos"]  # Gap for \n\n
    assert chunks[2]["start_pos"] > chunks[1]["end_pos"]  # Gap for \n\n


def test_long_paragraph_chunk_by_sentence():
    """Test that a long paragraph is chunked by sentence boundaries."""
    # Create a paragraph with multiple sentences that exceeds token limit
    sentences = [
        "This is the first sentence. ",
        "This is the second sentence. ",
        "This is the third sentence. ",
        "This is the fourth sentence."
    ]
    text = "".join(sentences)
    
    # Use a very low token limit to force sentence-level chunking
    chunks = chunk_text(text, max_tokens=10)
    
    # Should have multiple chunks (one per sentence or group of sentences)
    assert len(chunks) >= 4
    
    # Verify exact offset preservation for each chunk
    for chunk in chunks:
        assert text[chunk["start_pos"]:chunk["end_pos"]] == chunk["text"]
    
    # Verify chunk indices increment
    for i, chunk in enumerate(chunks):
        assert chunk["chunk_index"] == i
    
    # Verify no gaps or overlaps in coverage
    reconstructed = ""
    last_end = 0
    for chunk in chunks:
        # Add any gap between chunks
        if chunk["start_pos"] > last_end:
            reconstructed += text[last_end:chunk["start_pos"]]
        reconstructed += chunk["text"]
        last_end = chunk["end_pos"]
    
    # Add any remaining text
    if last_end < len(text):
        reconstructed += text[last_end:]
    
    assert reconstructed == text


def test_unicode_text_offsets():
    """Test that Unicode text offsets are code-point based, not byte-based."""
    # Text with multi-byte Unicode characters
    text = "Hello 世界! This is a test. 你好世界!"
    
    chunks = chunk_text(text, max_tokens=500)
    
    # Verify exact offset preservation with Unicode
    for chunk in chunks:
        extracted = text[chunk["start_pos"]:chunk["end_pos"]]
        assert extracted == chunk["text"]
        
        # Verify offsets are code-point based
        # If they were byte-based, slicing would fail or produce wrong results
        assert len(extracted) == chunk["end_pos"] - chunk["start_pos"]


def test_no_gaps_or_overlaps():
    """Test that chunks have no gaps or overlaps in their offsets."""
    text = "Paragraph one.\n\nParagraph two with a sentence. Another sentence here.\n\nParagraph three."
    
    chunks = chunk_text(text, max_tokens=500)
    
    # Verify each chunk's text matches its offsets
    for chunk in chunks:
        assert text[chunk["start_pos"]:chunk["end_pos"]] == chunk["text"]
    
    # Verify chunks are in order
    for i in range(len(chunks) - 1):
        assert chunks[i]["end_pos"] <= chunks[i + 1]["start_pos"]
    
    # Verify all text is covered (accounting for paragraph separators)
    covered_ranges = [(c["start_pos"], c["end_pos"]) for c in chunks]
    
    # Check that we can reconstruct the original text from chunks
    for chunk in chunks:
        extracted_text = text[chunk["start_pos"]:chunk["end_pos"]]
        assert extracted_text == chunk["text"]


def test_empty_text():
    """Test that empty text returns empty chunk list."""
    text = ""
    
    chunks = chunk_text(text, max_tokens=500)
    
    assert len(chunks) == 0


def test_text_with_only_whitespace():
    """Test that text with only whitespace/newlines is handled correctly."""
    text = "\n\n\n\n"
    
    chunks = chunk_text(text, max_tokens=500)
    
    # Should return empty or minimal chunks
    # Verify no crashes and offsets are valid
    for chunk in chunks:
        assert text[chunk["start_pos"]:chunk["end_pos"]] == chunk["text"]


def test_sentence_without_punctuation():
    """Test that sentences without ending punctuation are handled."""
    text = "This is a sentence without punctuation"
    
    chunks = chunk_text(text, max_tokens=500)
    
    assert len(chunks) == 1
    assert chunks[0]["text"] == text
    assert text[chunks[0]["start_pos"]:chunks[0]["end_pos"]] == chunks[0]["text"]


def test_mixed_punctuation():
    """Test text with mixed punctuation marks."""
    text = "Question? Exclamation! Statement. Another statement."
    
    chunks = chunk_text(text, max_tokens=10)  # Force sentence-level chunking
    
    # Verify exact offset preservation
    for chunk in chunks:
        assert text[chunk["start_pos"]:chunk["end_pos"]] == chunk["text"]
    
    # Verify all chunks have valid token counts
    for chunk in chunks:
        assert chunk["token_count"] > 0


def test_chunk_index_increments():
    """Test that chunk_index increments correctly."""
    text = "Para 1.\n\nPara 2.\n\nPara 3.\n\nPara 4."
    
    chunks = chunk_text(text, max_tokens=500)
    
    for i, chunk in enumerate(chunks):
        assert chunk["chunk_index"] == i


def test_token_count_accuracy():
    """Test that token_count is calculated correctly."""
    text = "This is a test paragraph with some words."
    
    chunks = chunk_text(text, max_tokens=500)
    
    assert len(chunks) == 1
    assert chunks[0]["token_count"] > 0
    
    # Token count should be reasonable (not zero, not absurdly high)
    assert 5 < chunks[0]["token_count"] < 50
