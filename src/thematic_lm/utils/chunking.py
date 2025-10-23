"""Text chunking utilities with exact offset preservation."""

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
