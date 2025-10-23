"""Type definitions for coder agent interfaces.

This module defines the TypedDict structures for the coder agent's
input and output contracts per internal/agents-coder@v1.
"""

from typing import TypedDict


class Quote(TypedDict):
    """Quote structure with exact offsets.
    
    Represents a text quote extracted from an interaction chunk with
    precise Unicode code-point offsets for traceability.
    """
    quote_id: str
    text: str
    interaction_id: str
    chunk_index: int
    start_pos: int
    end_pos: int


class Code(TypedDict):
    """Code structure with supporting quotes.
    
    Represents a thematic code with 1-3 supporting quotes that
    ground the code in the source text.
    """
    label: str
    quotes: list[Quote]


class TokenUsage(TypedDict):
    """Token usage tracking for LLM calls.
    
    Tracks prompt and completion tokens for cost monitoring
    and resource usage analysis.
    """
    prompt_tokens: int
    completion_tokens: int


class CoderResult(TypedDict):
    """Result from coder agent (internal/agents-coder@v1 interface).
    
    This is the provider contract for the coder agent interface.
    Contains generated codes with supporting quotes and token usage metadata.
    """
    codes: list[Code]
    token_usage: TokenUsage
