# Chunking Strategy Contract v1

## Purpose

The chunking strategy defines how long interactions are split into smaller pieces for processing by LLM agents. Proper chunking ensures that text fits within context windows while preserving semantic coherence.

## Tokenizer

### Specification
- **Tokenizer**: tiktoken with `cl100k_base` encoding (OpenAI GPT-4 tokenizer)
- **Library**: `tiktoken` Python package
- **Encoding**: `tiktoken.get_encoding("cl100k_base")`

### Rationale
- Matches OpenAI GPT-4 tokenization for accurate token counting
- Consistent with cost estimation and context window management
- Widely supported and well-documented

### Installation
```bash
pip install tiktoken
```

## Maximum Chunk Size

### Default Configuration
- **Maximum tokens per chunk**: 1024 tokens (default, configurable)
- **Configurable via**: `MAX_CHUNK_TOKENS` environment variable
- **Recommended range**: 512-2048 tokens

### Rationale
- 1024 tokens balances context preservation with processing efficiency
- Leaves room for prompt overhead (system prompt, instructions, etc.)
- Allows ~750-800 words of English text per chunk

## Boundary Detection

### Splitting Rules (Priority Order)

1. **Paragraph breaks** (`\n\n`): Preferred split point
   - Preserves semantic units (paragraphs)
   - Natural boundaries in most text types

2. **Sentence boundaries**: If no paragraph break within chunk size
   - Use sentence-ending punctuation (`.`, `!`, `?`) followed by space or newline
   - Preserves complete thoughts

3. **Never split mid-sentence**: Avoid breaking sentences
   - If sentence exceeds chunk size, include entire sentence in chunk (may exceed max slightly)
   - Better to have slightly oversized chunk than broken sentence

### Algorithm
```
1. Start with empty chunk
2. Add sentences/paragraphs until approaching max_tokens
3. If next unit would exceed max_tokens:
   a. If current chunk is empty, add unit anyway (don't split mid-sentence)
   b. Otherwise, finalize current chunk and start new chunk
4. Repeat until all text processed
```

## Newline Handling

### Normalization
- **Normalize `\r\n` to `\n`**: Convert Windows line endings to Unix
- **Preserve `\n` in chunks**: Maintain original line structure
- **Paragraph detection**: `\n\n` (two consecutive newlines) indicates paragraph break

### Rationale
- Consistent line ending handling across platforms
- Preserves document structure for better context
- Simplifies boundary detection logic

## Overlap Strategy

### V1: No Overlap
- **Chunks are sequential and non-overlapping**
- Each token appears in exactly one chunk
- Simpler implementation and cost-effective

### Future (Post-v1): Optional Overlap
- Consider adding configurable overlap (e.g., 50-100 tokens)
- Helps preserve context across chunk boundaries
- Useful for concepts that span boundaries

## Output Structure

### Chunk Object Schema

```json
{
  "chunk_index": 0,
  "text": "The actual chunk text...",
  "start_pos": 0,
  "end_pos": 245,
  "token_count": 52
}
```

### Fields
- `chunk_index` (integer): 0-based index of chunk within interaction
- `text` (string): The chunk content
- `start_pos` (integer): Unicode code-point offset in original text (0-based)
- `end_pos` (integer): Unicode code-point offset in original text (exclusive)
- `token_count` (integer): Estimated token count using tiktoken

### Array Structure
```json
{
  "interaction_id": "12345678-1234-5678-1234-567812345678",
  "original_text": "The full original text...",
  "chunks": [
    {
      "chunk_index": 0,
      "text": "First chunk...",
      "start_pos": 0,
      "end_pos": 245,
      "token_count": 52
    },
    {
      "chunk_index": 1,
      "text": "Second chunk...",
      "start_pos": 245,
      "end_pos": 512,
      "token_count": 58
    }
  ]
}
```

## Handling Edge Cases

### Very Short Interactions (< 100 tokens)
- **Strategy**: Single chunk, no splitting
- **Rationale**: Overhead of chunking not worth it for short text
- **Implementation**: If `token_count < 100`, return single chunk

### Very Long Interactions (> 10k tokens)
- **Strategy**: Split into multiple chunks following rules above
- **Rationale**: Necessary to fit within LLM context windows
- **Implementation**: Apply standard chunking algorithm
- **Note**: May result in 10+ chunks for very long documents

### Empty Interactions
- **Strategy**: Return empty chunks array
- **Validation**: Log warning, skip processing
- **Rationale**: No content to analyze

### Single-Sentence Interactions
- **Strategy**: Single chunk, even if > max_tokens
- **Rationale**: Cannot split mid-sentence
- **Note**: Rare edge case (most sentences < 1024 tokens)

## Implementation Example

### Python Implementation

```python
import tiktoken
from typing import List, Dict

def chunk_text(
    text: str,
    max_tokens: int = 1024,
    encoding_name: str = "cl100k_base"
) -> List[Dict]:
    """Chunk text into token-sized pieces.
    
    Args:
        text: Original text to chunk
        max_tokens: Maximum tokens per chunk
        encoding_name: Tiktoken encoding name
        
    Returns:
        List of chunk dictionaries with metadata
    """
    # Normalize line endings
    text = text.replace('\r\n', '\n')
    
    # Get tokenizer
    encoding = tiktoken.get_encoding(encoding_name)
    
    # Estimate total tokens
    total_tokens = len(encoding.encode(text))
    
    # Short text: single chunk
    if total_tokens < 100:
        return [{
            "chunk_index": 0,
            "text": text,
            "start_pos": 0,
            "end_pos": len(text),
            "token_count": total_tokens
        }]
    
    # Split on paragraph breaks
    paragraphs = text.split('\n\n')
    
    chunks = []
    current_chunk = []
    current_tokens = 0
    current_start_pos = 0
    
    for para in paragraphs:
        para_tokens = len(encoding.encode(para))
        
        if current_tokens + para_tokens > max_tokens and current_chunk:
            # Finalize current chunk
            chunk_text = '\n\n'.join(current_chunk)
            chunks.append({
                "chunk_index": len(chunks),
                "text": chunk_text,
                "start_pos": current_start_pos,
                "end_pos": current_start_pos + len(chunk_text),
                "token_count": current_tokens
            })
            
            # Start new chunk
            current_chunk = [para]
            current_tokens = para_tokens
            current_start_pos += len(chunk_text) + 2  # +2 for \n\n
        else:
            current_chunk.append(para)
            current_tokens += para_tokens
    
    # Add final chunk
    if current_chunk:
        chunk_text = '\n\n'.join(current_chunk)
        chunks.append({
            "chunk_index": len(chunks),
            "text": chunk_text,
            "start_pos": current_start_pos,
            "end_pos": current_start_pos + len(chunk_text),
            "token_count": current_tokens
        })
    
    return chunks
```

## Validation Rules

### Chunk Validation
- `chunk_index` must be ≥ 0 and sequential (0, 1, 2, ...)
- `text` must be non-empty
- `start_pos` < `end_pos`
- `start_pos` must be ≥ 0
- `token_count` must be > 0
- `token_count` should be ≤ max_tokens (soft limit, may exceed for single sentences)

### Chunks Array Validation
- Chunks must be sequential (no gaps in chunk_index)
- Chunks must be non-overlapping (chunk[i].end_pos == chunk[i+1].start_pos)
- First chunk must start at position 0
- Last chunk must end at len(original_text)
- Concatenating all chunk texts should equal original text

## Versioning

### Breaking Changes (Require v2)
- Changing tokenizer (e.g., switching from cl100k_base to another encoding)
- Changing overlap strategy (e.g., adding overlap when v1 has none)
- Changing boundary detection rules significantly

### Non-Breaking Changes (Allowed in v1)
- Adjusting max_tokens default (if configurable)
- Improving boundary detection heuristics (if results are compatible)
- Adding optional metadata fields to chunk objects
