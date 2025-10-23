"""Quote ID encoding and decoding utilities.

Implements the models/quote_id@v1 contract for quote identifier format.
"""

import re
from typing import Optional


# Canonical regex per models/quote_id@v1
QUOTE_ID_PATTERN = re.compile(
    r'^(?P<interaction_id>[a-f0-9-]+)'
    r'(?::msg_(?P<msg_index>\d+))?'
    r':ch_(?P<chunk_index>\d+)'
    r':(?P<start_pos>\d+)-(?P<end_pos>\d+)$'
)


def encode_quote_id(
    interaction_id: str,
    chunk_index: int,
    start_pos: int,
    end_pos: int,
    msg_index: Optional[int] = None
) -> str:
    """Encode quote ID per models/quote_id@v1.
    
    Format: {interaction_id}[:msg_{n}]:ch_{chunk_index}:{start_pos}-{end_pos}
    
    Args:
        interaction_id: UUID of the interaction
        chunk_index: Zero-based chunk index
        start_pos: Unicode code-point start offset
        end_pos: Unicode code-point end offset
        msg_index: Optional message index for email threads
        
    Returns:
        Encoded quote ID string
    """
    if msg_index is not None:
        return f"{interaction_id}:msg_{msg_index}:ch_{chunk_index}:{start_pos}-{end_pos}"
    return f"{interaction_id}:ch_{chunk_index}:{start_pos}-{end_pos}"


def decode_quote_id(quote_id: str) -> dict:
    """Decode quote ID per models/quote_id@v1.
    
    Args:
        quote_id: Encoded quote ID string
        
    Returns:
        Dictionary with interaction_id, chunk_index, start_pos, end_pos, msg_index
        
    Raises:
        ValueError: If quote_id doesn't match canonical pattern
    """
    match = QUOTE_ID_PATTERN.match(quote_id)
    if not match:
        raise ValueError(f"Invalid quote_id format: {quote_id}")
    
    return {
        "interaction_id": match.group("interaction_id"),
        "msg_index": int(match.group("msg_index")) if match.group("msg_index") else None,
        "chunk_index": int(match.group("chunk_index")),
        "start_pos": int(match.group("start_pos")),
        "end_pos": int(match.group("end_pos"))
    }
