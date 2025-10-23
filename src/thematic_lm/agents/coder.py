"""Coder agent implementation for generating codes with identity perspectives.

This module implements the CoderAgent class that analyzes text chunks and
generates descriptive codes with supporting quotes using LLM-based analysis.
"""

import os
from typing import List, Optional, Any
import structlog
from openai import AsyncOpenAI

from thematic_lm.utils.identities import Identity
from thematic_lm.utils.json_safety import parse_json_array
from thematic_lm.utils.quotes import normalize_quote_span
from thematic_lm.utils.quote_id import encode_quote_id
from thematic_lm.utils.retry import call_with_retry
from thematic_lm.agents.types import Code, Quote, CoderResult, TokenUsage

logger = structlog.get_logger(__name__)

CODER_PROMPT_TEMPLATE = """Analyze the following text and generate 1-3 descriptive codes that capture key themes or concepts.

For each code:
1. Provide a concise label (max 200 characters)
2. Extract 1-3 representative quotes from the text that support the code
3. Ensure each quote is VERBATIM from the text (exact copy, no modifications)
4. For each quote, provide text, start_pos, and end_pos as Unicode code-point offsets

IMPORTANT: Respond ONLY with a JSON array (no other text, no markdown fences, no explanations).

Text to analyze:
{text}

Expected JSON array format:
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
]"""


class CoderAgent:
    """Coder agent that generates codes with identity perspective.
    
    The agent analyzes text chunks and produces descriptive codes with
    supporting quotes. Each agent operates with a specific identity
    perspective to capture diverse interpretations.
    """
    
    def __init__(
        self,
        identity: Identity,
        model: str = "gpt-4o",
        dry_run: bool = False,
        openai_client: Optional[AsyncOpenAI] = None
    ):
        """Initialize coder agent with identity and configuration.
        
        Args:
            identity: Identity configuration with prompt_prefix
            model: LLM model to use (default: gpt-4o)
            dry_run: If True, return mock results without API calls
            openai_client: Optional OpenAI client (for testing)
        """
        self.identity = identity
        self.model = model
        self.dry_run = dry_run or os.getenv("DRY_RUN") == "1"
        self._client = openai_client
        
        # Only initialize OpenAI client if not in dry_run mode and no client provided
        if not self.dry_run and self._client is None:
            self._client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def _build_prompt(self, chunk_text: str) -> str:
        """Build prompt with chunk text.
        
        Formats the coder prompt template with the provided chunk text,
        creating a complete prompt for the LLM.
        
        Args:
            chunk_text: Text chunk to analyze
            
        Returns:
            Formatted prompt string ready for LLM
        """
        return CODER_PROMPT_TEMPLATE.format(text=chunk_text)
    
    async def _call_llm(self, messages: List[dict]) -> dict:
        """Call LLM with retry logic.
        
        Returns dict with 'content' and 'usage' keys.
        Usage contains prompt_tokens and completion_tokens.
        
        Args:
            messages: List of message dicts with role and content
            
        Returns:
            Response dict with content and usage metadata
        """
        async def _make_request() -> dict:
            """Make the actual OpenAI API request."""
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,  # type: ignore
                temperature=0.7,
                max_tokens=1000
            )
            
            # Extract content and usage
            content = response.choices[0].message.content or ""
            usage = response.usage
            
            # Log token usage at INFO level (no content)
            if usage:
                logger.info(
                    "LLM call completed",
                    model=self.model,
                    prompt_tokens=usage.prompt_tokens,
                    completion_tokens=usage.completion_tokens,
                    total_tokens=usage.total_tokens
                )
            
            return {
                "content": content,
                "usage": {
                    "prompt_tokens": usage.prompt_tokens if usage else 0,
                    "completion_tokens": usage.completion_tokens if usage else 0
                }
            }
        
        # Use retry logic
        return await call_with_retry(
            _make_request,
            max_attempts=3,
            base_delay=1.0,
            timeout=30.0
        )
    
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
            token_usage: TokenUsage = {
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
        """Return mock CoderResult for DRY_RUN mode.
        
        Args:
            chunk: Chunk dict with text and chunk_index
            interaction_id: UUID of the interaction
            
        Returns:
            Mock CoderResult with valid structure
        """
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
