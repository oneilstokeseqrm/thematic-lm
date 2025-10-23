"""Quote validation and repair utilities."""

from typing import Optional, Tuple
import structlog

logger = structlog.get_logger(__name__)


def normalize_quote_span(
    quote_text: str,
    chunk_text: str,
    start_pos: Optional[int] = None,
    end_pos: Optional[int] = None
) -> Optional[Tuple[int, int]]:
    """Validate and repair quote span offsets.
    
    If offsets are provided but don't match the quote text, attempts to locate
    the quote in the chunk. Returns None if quote cannot be validated.
    
    Args:
        quote_text: The quote text to validate
        chunk_text: The chunk text containing the quote
        start_pos: Claimed start position (Unicode code-point offset)
        end_pos: Claimed end position (Unicode code-point offset)
        
    Returns:
        Tuple of (start_pos, end_pos) if valid, None otherwise
    """
    # If offsets provided, validate them first
    if start_pos is not None and end_pos is not None:
        if 0 <= start_pos < end_pos <= len(chunk_text):
            extracted = chunk_text[start_pos:end_pos]
            if extracted == quote_text:
                return (start_pos, end_pos)
    
    # Attempt repair by finding quote in chunk
    try:
        found_start = chunk_text.index(quote_text)
        found_end = found_start + len(quote_text)
        logger.info(
            "Repaired quote offsets",
            original_start=start_pos,
            original_end=end_pos,
            repaired_start=found_start,
            repaired_end=found_end
        )
        return (found_start, found_end)
    except ValueError:
        logger.warning(
            "Quote not found in chunk",
            quote_length=len(quote_text),
            chunk_length=len(chunk_text)
        )
        return None
