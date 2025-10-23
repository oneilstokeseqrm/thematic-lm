# Design: Identity-Based Coder Agents

## Architecture Overview

Coder agents are LLM-powered agents that analyze interactions and generate descriptive codes with supporting quotes. Each agent operates with a specific identity perspective (loaded from identities.yaml) to capture diverse interpretations. This design is self-contained for Phase B Part 1 and does not depend on cost management or orchestrator components.

## Module Structure

```
src/thematic_lm/
├── utils/
│   ├── identities.py      # Identity loading and validation
│   ├── json_safety.py     # Safe JSON parsing with fallback strategies
│   ├── quotes.py          # Quote validation and repair
│   ├── quote_id.py        # Quote ID encoding/decoding
│   ├── chunking.py        # Text chunking with exact offset preservation
│   └── retry.py           # Retry logic with exponential backoff
└── agents/
    ├── types.py           # Quote and Code TypedDicts
    └── coder.py           # CoderAgent implementation
```

## Utilities Layer

### src/thematic_lm/utils/identities.py

```python
from dataclasses import dataclass
from functools import lru_cache
from typing import List, Optional
import yaml

@dataclass
class Identity:
    """Identity configuration for coder agents.
    
    Required fields: id, name, prompt_prefix
    Optional fields: description
    """
    id: str
    name: str
    prompt_prefix: str
    description: Optional[str] = None

@lru_cache(maxsize=1)
def load_identities(path: str = "identities.yaml") -> List[Identity]:
    """Load and cache identities from YAML.
    
    Validates required fields (id, name, prompt_prefix) and fails fast on errors.
    Optional fields (description) are accepted but not required.
    
    Args:
        path: Path to identities.yaml file
        
    Returns:
        List of validated Identity objects
        
    Raises:
        FileNotFoundError: If identities file not found
        ValueError: If required fields missing or no identities defined
    """
    with open(path) as f:
        config = yaml.safe_load(f)
    
    if "identities" not in config:
        raise ValueError("No 'identities' key in identities.yaml")
    
    identities = []
    required_fields = ["id", "name", "prompt_prefix"]
    
    for item in config["identities"]:
        missing = [k for k in required_fields if k not in item]
        if missing:
            raise ValueError(f"Identity missing required fields {missing}: {item}")
        
        identities.append(Identity(**item))
    
    if not identities:
        raise ValueError("No identities defined in identities.yaml")
    
    return identities
```

### src/thematic_lm/utils/json_safety.py

```python
import json
import re
from typing import List, Dict, Any
import structlog

logger = structlog.get_logger(__name__)

def parse_json_array(content: str) -> List[Dict[str, Any]]:
    """Parse JSON array from LLM output with fallback strategies (Option A).
    
    Strategies (in order):
    1. Direct JSON parsing
    2. Extract from ```json fenced block (with language tag)
    3. Extract from bare ``` fenced block (no language tag)
    4. Extract first JSON array using non-greedy regex
    
    If result is dict with "codes" key, normalize to list and log WARNING.
    
    Args:
        content: Raw LLM output string
        
    Returns:
        Parsed list of dictionaries, or empty list on failure
    """
    # Strategy 1: Direct parse
    try:
        result = json.loads(content)
        if isinstance(result, list):
            return result
        if isinstance(result, dict) and "codes" in result:
            logger.warning("LLM returned dict with 'codes' key; normalizing to array")
            return result["codes"]
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: Extract from ```json fenced block
    fenced_match = re.search(r'```json\s*\n(.*?)\n```', content, re.DOTALL)
    if fenced_match:
        try:
            result = json.loads(fenced_match.group(1))
            if isinstance(result, list):
                return result
            if isinstance(result, dict) and "codes" in result:
                logger.warning("LLM returned dict with 'codes' key; normalizing to array")
                return result["codes"]
        except json.JSONDecodeError:
            pass
    
    # Strategy 3: Extract from bare ``` fenced block
    bare_fenced_match = re.search(r'```\s*\n(.*?)\n```', content, re.DOTALL)
    if bare_fenced_match:
        try:
            result = json.loads(bare_fenced_match.group(1))
            if isinstance(result, list):
                return result
            if isinstance(result, dict) and "codes" in result:
                logger.warning("LLM returned dict with 'codes' key; normalizing to array")
                return result["codes"]
        except json.JSONDecodeError:
            pass
    
    # Strategy 4: Extract first JSON array using non-greedy regex
    array_match = re.search(r'\[[\s\S]*?\]', content)
    if array_match:
        try:
            result = json.loads(array_match.group(0))
            if isinstance(result, list):
                return result
        except json.JSONDecodeError:
            pass
    
    logger.warning("Failed to parse JSON from LLM output", content_length=len(content))
    return []
```

### src/thematic_lm/utils/quotes.py

```python
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
        logger.info("Repaired quote offsets", 
                   original_start=start_pos, 
                   original_end=end_pos,
                   repaired_start=found_start,
                   repaired_end=found_end)
        return (found_start, found_end)
    except ValueError:
        logger.warning("Quote not found in chunk", 
                      quote_length=len(quote_text),
                      chunk_length=len(chunk_text))
        return None
```

### src/thematic_lm/utils/quote_id.py

```python
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
```

### src/thematic_lm/utils/chunking.py

```python
from typing import List, TypedDict
import re
import tiktoken

class Chunk(TypedDict):
    """Chunk structure per models/chunking@v1."""
    chunk_index: int
    text: str
    start_pos: int
    end_pos: int
    token_count: int

def chunk_text(
    text: str,
    max_tokens: int = 500,
    encoding_name: str = "cl100k_base"
) -> List[Chunk]:
    """Chunk text by paragraphs then sentences, preserving exact offsets.
    
    Uses regex-based span detection to avoid str.index accumulation bugs.
    Chunks are created by slicing the original text (never rejoining).
    This ensures Unicode code-point offsets remain accurate.
    
    Args:
        text: Original text to chunk
        max_tokens: Maximum tokens per chunk
        encoding_name: Tokenizer encoding (default: cl100k_base for GPT-4)
        
    Returns:
        List of Chunk dictionaries with exact offsets
    """
    encoding = tiktoken.get_encoding(encoding_name)
    chunks: List[Chunk] = []
    chunk_index = 0
    
    # Find paragraph spans using regex (handles \n\n boundaries)
    para_pattern = re.compile(r'(.*?)(?:\n\n|$)', re.DOTALL)
    
    for para_match in para_pattern.finditer(text):
        para_start, para_end = para_match.span(1)
        if para_start == para_end:  # Skip empty matches at end
            continue
            
        para_text = text[para_start:para_end]
        para_tokens = len(encoding.encode(para_text))
        
        if para_tokens <= max_tokens:
            # Paragraph fits in one chunk
            chunks.append({
                "chunk_index": chunk_index,
                "text": para_text,
                "start_pos": para_start,
                "end_pos": para_end,
                "token_count": para_tokens
            })
            chunk_index += 1
        else:
            # Split paragraph by sentences using regex
            sent_pattern = re.compile(r'[^.!?]+[.!?]\s*|[^.!?]+$')
            
            for sent_match in sent_pattern.finditer(para_text):
                sent_rel_start, sent_rel_end = sent_match.span()
                sent_abs_start = para_start + sent_rel_start
                sent_abs_end = para_start + sent_rel_end
                
                sent_text = text[sent_abs_start:sent_abs_end]
                sent_tokens = len(encoding.encode(sent_text))
                
                chunks.append({
                    "chunk_index": chunk_index,
                    "text": sent_text,
                    "start_pos": sent_abs_start,
                    "end_pos": sent_abs_end,
                    "token_count": sent_tokens
                })
                chunk_index += 1
    
    return chunks
```

### src/thematic_lm/utils/retry.py

```python
import asyncio
import random
from typing import Awaitable, Callable, TypeVar, Any
import structlog

logger = structlog.get_logger(__name__)

T = TypeVar('T')

async def call_with_retry(
    fn: Callable[..., Awaitable[T]],
    max_attempts: int = 3,
    base_delay: float = 1.0,
    timeout: float = 30.0,
    *args: Any,
    **kwargs: Any
) -> T:
    """Call async function with exponential backoff retry.
    
    Args:
        fn: Async function to call
        max_attempts: Maximum retry attempts
        base_delay: Base delay in seconds (doubled each retry)
        timeout: Timeout per attempt in seconds
        *args: Positional arguments for fn
        **kwargs: Keyword arguments for fn
        
    Returns:
        Result from fn
        
    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    
    for attempt in range(max_attempts):
        try:
            result = await asyncio.wait_for(fn(*args, **kwargs), timeout=timeout)
            
            if attempt > 0:
                logger.info("Call succeeded after retry", attempt=attempt + 1)
            
            return result
            
        except asyncio.TimeoutError as e:
            last_exception = e
            logger.warning("Call timed out", 
                         attempt=attempt + 1, 
                         max_attempts=max_attempts,
                         timeout=timeout)
            
        except Exception as e:
            last_exception = e
            logger.warning("Call failed", 
                         attempt=attempt + 1, 
                         max_attempts=max_attempts,
                         error=str(e))
        
        if attempt < max_attempts - 1:
            # Add jitter to prevent thundering herd
            delay = base_delay * (2 ** attempt) + random.uniform(0, 0.1)
            await asyncio.sleep(delay)
    
    logger.warning("All retry attempts failed", max_attempts=max_attempts)
    raise last_exception
```

## Agent Types

### src/thematic_lm/agents/types.py

```python
from typing import TypedDict

class Quote(TypedDict):
    """Quote structure with exact offsets."""
    quote_id: str
    text: str
    interaction_id: str
    chunk_index: int
    start_pos: int
    end_pos: int

class Code(TypedDict):
    """Code structure with supporting quotes."""
    label: str
    quotes: list[Quote]

class TokenUsage(TypedDict):
    """Token usage tracking."""
    prompt_tokens: int
    completion_tokens: int

class CoderResult(TypedDict):
    """Result from coder agent (internal/agents-coder@v1 interface).
    
    This is the provider contract for the coder agent interface.
    """
    codes: list[Code]
    token_usage: TokenUsage
```

## Agent Implementation

### src/thematic_lm/agents/coder.py

```python
import os
from typing import List, Optional
import structlog

from thematic_lm.utils.identities import Identity
from thematic_lm.utils.json_safety import parse_json_array
from thematic_lm.utils.quotes import normalize_quote_span
from thematic_lm.utils.quote_id import encode_quote_id
from thematic_lm.utils.retry import call_with_retry
from thematic_lm.agents.types import Code, Quote

logger = structlog.get_logger(__name__)

CODER_PROMPT_TEMPLATE = """
Analyze the following text and generate 1-3 descriptive codes that capture key themes or concepts.

For each code:
1. Provide a concise label (max 200 characters)
2. Extract 1-3 representative quotes from the text that support the code
3. Ensure each quote is verbatim from the text
4. For each quote, provide text, start_pos, and end_pos as Unicode code-point offsets

Text to analyze:
{text}

Respond ONLY with a JSON array (no other text):
[
  {{
    "label": "Code label here",
    "quotes": [
      {{
        "text": "Exact quote from text",
        "start_pos": 0,
        "end_pos": 50
      }}
    ]
  }}
]
"""

class CoderAgent:
    """Coder agent that generates codes with identity perspective."""
    
    def __init__(
        self,
        identity: Identity,
        model: str = "gpt-4o",
        dry_run: bool = False
    ):
        self.identity = identity
        self.model = model
        self.dry_run = dry_run or os.getenv("DRY_RUN") == "1"
    
    def _build_prompt(self, chunk_text: str) -> str:
        """Build prompt with chunk text."""
        return CODER_PROMPT_TEMPLATE.format(text=chunk_text)
    
    async def _call_llm(self, messages: List[dict]) -> dict:
        """Call LLM with retry logic.
        
        Returns dict with 'content' and 'usage' keys.
        Usage contains prompt_tokens and completion_tokens.
        """
        # This will be implemented with actual OpenAI client
        # For now, placeholder that will be mocked in tests
        raise NotImplementedError("LLM client integration pending")
    
    async def code_chunk(
        self,
        chunk: dict,
        interaction_id: str
    ) -> CoderResult:
        """Generate codes for a single chunk.
        
        Args:
            chunk: Chunk dict with text, chunk_index, start_pos, end_pos
            interaction_id: UUID of the interaction
            
        Returns:
            CoderResult with codes and token_usage (internal/agents-coder@v1 interface)
        """
        if self.dry_run:
            return self._mock_result(chunk, interaction_id)
        
        # Build messages
        messages = [
            {"role": "system", "content": self.identity.prompt_prefix},
            {"role": "user", "content": self._build_prompt(chunk["text"])}
        ]
        
        # Call LLM with retry
        try:
            response = await call_with_retry(
                self._call_llm,
                max_attempts=3,
                base_delay=1.0,
                timeout=30.0,
                messages=messages
            )
            token_usage = {
                "prompt_tokens": response["usage"]["prompt_tokens"],
                "completion_tokens": response["usage"]["completion_tokens"]
            }
        except Exception as e:
            logger.warning("LLM call failed after retries", error=str(e))
            return {
                "codes": [],
                "token_usage": {"prompt_tokens": 0, "completion_tokens": 0}
            }
        
        # Parse JSON safely
        raw_codes = parse_json_array(response["content"])
        
        # Validate and repair quotes
        codes: List[Code] = []
        for raw_code in raw_codes[:3]:  # Enforce max 3 codes
            if "label" not in raw_code or "quotes" not in raw_code:
                continue
            
            # Process quotes array (1-3 quotes per code)
            valid_quotes: List[Quote] = []
            for raw_quote in raw_code["quotes"][:3]:  # Enforce max 3 quotes per code
                if "text" not in raw_quote:
                    continue
                
                # Normalize quote span
                span = normalize_quote_span(
                    quote_text=raw_quote["text"],
                    chunk_text=chunk["text"],
                    start_pos=raw_quote.get("start_pos"),
                    end_pos=raw_quote.get("end_pos")
                )
                
                if span is None:
                    logger.warning("Dropping invalid quote", 
                                 label=raw_code["label"],
                                 quote_text=raw_quote["text"][:50])
                    continue
                
                start_pos, end_pos = span
                
                # Encode quote_id
                quote_id = encode_quote_id(
                    interaction_id=interaction_id,
                    chunk_index=chunk["chunk_index"],
                    start_pos=start_pos,
                    end_pos=end_pos
                )
                
                # Build Quote
                quote: Quote = {
                    "quote_id": quote_id,
                    "text": raw_quote["text"],
                    "interaction_id": interaction_id,
                    "chunk_index": chunk["chunk_index"],
                    "start_pos": start_pos,
                    "end_pos": end_pos
                }
                
                valid_quotes.append(quote)
            
            # Only add code if it has at least 1 valid quote
            if valid_quotes:
                code: Code = {
                    "label": raw_code["label"],
                    "quotes": valid_quotes
                }
                codes.append(code)
            else:
                logger.warning("Dropping code with no valid quotes", label=raw_code["label"])
        
        return {
            "codes": codes,
            "token_usage": token_usage
        }
    
    def _mock_result(self, chunk: dict, interaction_id: str) -> CoderResult:
        """Return mock CoderResult for DRY_RUN mode."""
        quote_id = encode_quote_id(
            interaction_id=interaction_id,
            chunk_index=chunk["chunk_index"],
            start_pos=0,
            end_pos=20
        )
        
        return {
            "codes": [{
                "label": f"Mock code for {self.identity.id}",
                "quotes": [{
                    "quote_id": quote_id,
                    "text": chunk["text"][:20],
                    "interaction_id": interaction_id,
                    "chunk_index": chunk["chunk_index"],
                    "start_pos": 0,
                    "end_pos": 20
                }]
            }],
            "token_usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50
            }
        }
```

## Design Decisions

### No Cost Calculation in Phase B Part 1
- Token usage (prompt_tokens, completion_tokens) is tracked from provider metadata
- No pricing or cost calculation logic in this phase
- Cost management deferred to future orchestrator component

### Exact Offset Preservation
- All chunking done by slicing original text (never rejoining)
- Unicode code-point offsets maintained throughout pipeline
- Quote validation includes repair attempt via text search

### JSON Safety
- Four strategies + dict normalization: direct → ```json fenced → bare ``` fenced → regex extraction
- If result is dict with "codes" key, normalize to list and log WARNING
- Failures logged at WARNING level (no content at INFO)
- Empty list returned on parse failure (no crash)

### DRY_RUN and LIVE_TESTS
- DRY_RUN=1 returns mock codes without API calls
- LIVE_TESTS=1 gates integration tests with real API
- Both flags respected throughout implementation

### Retry Strategy
- Max 3 attempts with exponential backoff
- Jitter added to prevent thundering herd
- Transient failures (timeout, 5xx) retried
- Success after retry logged at INFO level

## Dependencies

- **models/chunking@v1**: Text chunking strategy with exact offsets
- **models/quote_id@v1**: Quote ID encoding format with optional msg_{n}

## External Dependencies

- **OpenAI GPT-4o**: Code generation (implementation pending)
- **tiktoken**: Token counting for chunking
- **PyYAML**: Identity configuration loading
- **structlog**: Structured logging
