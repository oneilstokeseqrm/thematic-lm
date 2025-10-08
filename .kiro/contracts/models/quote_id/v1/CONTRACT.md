# Quote ID Encoding Contract v1

## Purpose

Quote IDs provide unique, traceable identifiers for text excerpts extracted from interactions. They encode the source interaction, chunk position, and character offsets, enabling precise retrieval of the original context.

## Format Specification

### Simple Interactions

For single-message interactions (social media posts, single emails, etc.):

```
{interaction_id}:ch_{chunk_index}:{start_pos}-{end_pos}
```

**Components**:
- `interaction_id`: UUID of the source interaction (format: 8-4-4-4-12 hex digits)
- `ch_{chunk_index}`: Chunk index within the interaction (0-based integer)
- `start_pos`: Start position in original text (Unicode code-point offset, 0-based)
- `end_pos`: End position in original text (Unicode code-point offset, exclusive)

**Example**:
```
12345678-1234-5678-1234-567812345678:ch_0:45-123
```

### Email Threads

For multi-message interactions (email threads, conversation threads):

```
{interaction_id}:msg_{message_index}:ch_{chunk_index}:{start_pos}-{end_pos}
```

**Additional Component**:
- `msg_{message_index}`: Message index within the thread (0-based integer)

**Example**:
```
12345678-1234-5678-1234-567812345678:msg_2:ch_1:100-250
```

## Character Indexing

### Unicode Code-Point Offsets

**Important**: Offsets are Unicode code-point indices, NOT byte offsets.

- **0-based indexing**: First character is at position 0
- **Exclusive end**: `end_pos` points to the position after the last character
- **Code-point counting**: Each Unicode character (including emoji, accented characters) counts as 1

### Examples with Unicode

#### Example 1: ASCII text
```
Text: "Hello world"
Quote: "world"
Offsets: start_pos=6, end_pos=11
Quote ID: {uuid}:ch_0:6-11
```

#### Example 2: Emoji
```
Text: "I love 🌍 Earth"
Quote: "🌍 Earth"
Offsets: start_pos=7, end_pos=14
Quote ID: {uuid}:ch_0:7-14

Note: 🌍 is 1 code-point, not 4 bytes
```

#### Example 3: Accented characters
```
Text: "Café résumé"
Quote: "résumé"
Offsets: start_pos=5, end_pos=11
Quote ID: {uuid}:ch_0:5-11

Note: é is 1 code-point (U+00E9), not 2 bytes
```

## Canonical Regex Pattern

All quote IDs must match this regex:

```regex
^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}:(msg_\d+:)?ch_\d+:\d+-\d+$
```

**Pattern Breakdown**:
- `[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}`: UUID (lowercase hex)
- `(msg_\d+:)?`: Optional message index (for email threads)
- `ch_\d+`: Chunk index (required)
- `\d+-\d+`: Start and end positions (required)

## Validation Rules

### Format Validation
1. Must match canonical regex pattern
2. UUID must be valid (lowercase hex, correct format)
3. Chunk index must be ≥ 0
4. Message index (if present) must be ≥ 0
5. Start position must be < end position
6. Start position must be ≥ 0

### Semantic Validation
1. `interaction_id` should exist in database (soft validation)
2. `chunk_index` should be valid for the interaction (< total chunks)
3. `message_index` (if present) should be valid for the thread (< total messages)
4. Offsets should be within bounds of the original text

### Error Handling
- Invalid format: Reject with validation error
- Missing interaction: Log warning, allow (may be deleted interaction)
- Out-of-bounds offsets: Log warning, allow (may be chunking inconsistency)

## Edge Cases

### Single-Character Quotes
```
Text: "A B C"
Quote: "B"
Offsets: start_pos=2, end_pos=3
Quote ID: {uuid}:ch_0:2-3
```

### Empty Quotes (Invalid)
```
start_pos=5, end_pos=5  # INVALID: start_pos must be < end_pos
```

### Multi-Chunk Quotes (Not Supported)
Quotes cannot span multiple chunks. If a concept spans chunks, select the most representative chunk.

### Newlines and Whitespace
Newlines and whitespace count as code-points:
```
Text: "Line 1\nLine 2"
Quote: "Line 2"
Offsets: start_pos=7, end_pos=13
Quote ID: {uuid}:ch_0:7-13

Note: \n is 1 code-point at position 6
```

## Encoding/Decoding Examples

### Python Implementation

```python
import re
from typing import Optional, Tuple

QUOTE_ID_PATTERN = re.compile(
    r'^([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}):'
    r'(msg_(\d+):)?ch_(\d+):(\d+)-(\d+)$'
)

def encode_quote_id(
    interaction_id: str,
    chunk_index: int,
    start_pos: int,
    end_pos: int,
    message_index: Optional[int] = None
) -> str:
    """Encode a quote ID from components."""
    if start_pos >= end_pos:
        raise ValueError(f"start_pos ({start_pos}) must be < end_pos ({end_pos})")
    
    if message_index is not None:
        return f"{interaction_id}:msg_{message_index}:ch_{chunk_index}:{start_pos}-{end_pos}"
    return f"{interaction_id}:ch_{chunk_index}:{start_pos}-{end_pos}"

def decode_quote_id(quote_id: str) -> dict:
    """Decode a quote ID into components."""
    match = QUOTE_ID_PATTERN.match(quote_id)
    if not match:
        raise ValueError(f"Invalid quote ID format: {quote_id}")
    
    interaction_id, _, message_index, chunk_index, start_pos, end_pos = match.groups()
    
    return {
        "interaction_id": interaction_id,
        "message_index": int(message_index) if message_index else None,
        "chunk_index": int(chunk_index),
        "start_pos": int(start_pos),
        "end_pos": int(end_pos)
    }

# Example usage
quote_id = encode_quote_id(
    "12345678-1234-5678-1234-567812345678",
    chunk_index=0,
    start_pos=45,
    end_pos=123
)
# Result: "12345678-1234-5678-1234-567812345678:ch_0:45-123"

components = decode_quote_id(quote_id)
# Result: {
#     "interaction_id": "12345678-1234-5678-1234-567812345678",
#     "message_index": None,
#     "chunk_index": 0,
#     "start_pos": 45,
#     "end_pos": 123
# }
```

## Versioning

### Breaking Changes (Require v2)
- Changing format structure (e.g., adding required components)
- Changing indexing scheme (e.g., 1-based instead of 0-based)
- Changing character counting (e.g., bytes instead of code-points)

### Non-Breaking Changes (Allowed in v1)
- Adding optional components (must be backward-compatible)
- Clarifying documentation
- Adding validation rules (if they don't reject previously valid IDs)
