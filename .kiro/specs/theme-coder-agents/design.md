# Design: Theme Coder Agents

## Architecture Overview

Theme coder agents generate theme proposals from codebook analysis with automatic compression for large codebooks. They use LLMLingua for intelligent compression with fallback to simple truncation.

```
┌─────────────────────────────────────────────────────────────┐
│                 Theme Coder Agent                            │
│  ┌────────────────────────────────────────────────────┐    │
│  │              Compression Pipeline                   │    │
│  │                                                      │    │
│  │  [Codebook] → [Size Check] → [Compression Gate]    │    │
│  │                     ↓              ↓                │    │
│  │              [LLMLingua] ←→ [Fallback Truncation]   │    │
│  │                     ↓                               │    │
│  │              [Theme Generation] → [Themes]          │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  LLMLingua ←→ LangChain DocumentCompressor                 │
│  OpenAI GPT-4o ←→ Theme generation                         │
│  tiktoken ←→ Token counting                                 │
└─────────────────────────────────────────────────────────────┘
```

## Key Classes/Functions

### ThemeCoderAgent

```python
from typing import List, Dict, Optional
import tiktoken
from langchain.schema import Document
from langchain.document_compressors import LLMLinguaCompressor

class ThemeCoderAgent:
    def __init__(
        self,
        openai_client,
        max_codes_threshold: int = 100,
        max_tokens_threshold: int = 50000
    ):
        self.openai_client = openai_client
        self.max_codes_threshold = max_codes_threshold
        self.max_tokens_threshold = max_tokens_threshold
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # Initialize LLMLingua compressor
        try:
            self.compressor = LLMLinguaCompressor(
                model_name="microsoft/llmlingua-2-xlm-roberta-large-meetingbank",
                use_llmlingua2=True
            )
            self.llmlingua_available = True
        except Exception:
            self.compressor = None
            self.llmlingua_available = False
    
    async def generate_themes(self, codebook: Dict) -> List[Dict]:
        """Generate themes from codebook."""
        # Check if compression is needed
        needs_compression = self._needs_compression(codebook)
        
        if needs_compression:
            compressed_codebook = await self._compress_codebook(codebook)
            input_codebook = compressed_codebook
        else:
            input_codebook = codebook
        
        # Generate themes using LLM
        themes = await self._generate_themes_llm(input_codebook)
        
        return themes
    
    def _needs_compression(self, codebook: Dict) -> bool:
        """Check if codebook needs compression."""
        codes = codebook.get("codes", [])
        
        # Check code count threshold
        if len(codes) > self.max_codes_threshold:
            return True
        
        # Check token count threshold
        codebook_text = self._codebook_to_text(codebook)
        token_count = len(self.tokenizer.encode(codebook_text))
        
        return token_count > self.max_tokens_threshold
    
    async def _compress_codebook(self, codebook: Dict) -> Dict:
        """Compress codebook using LLMLingua or fallback."""
        if self.llmlingua_available:
            try:
                return await self._compress_with_llmlingua(codebook)
            except Exception as e:
                logger.warning(f"LLMLingua compression failed: {e}, falling back to truncation")
                return self._compress_with_truncation(codebook)
        else:
            logger.info("LLMLingua not available, using truncation")
            return self._compress_with_truncation(codebook)
```

## Compression Gate Logic

### Size Thresholds

```python
def _needs_compression(self, codebook: Dict) -> bool:
    """Determine if compression is needed."""
    codes = codebook.get("codes", [])
    
    # Threshold 1: Code count
    if len(codes) > 100:
        logger.info(f"Compression triggered: {len(codes)} codes > 100")
        return True
    
    # Threshold 2: Token count
    codebook_text = self._codebook_to_text(codebook)
    tokens = self.tokenizer.encode(codebook_text)
    
    if len(tokens) > 50000:
        logger.info(f"Compression triggered: {len(tokens)} tokens > 50k")
        return True
    
    logger.info(f"No compression needed: {len(codes)} codes, {len(tokens)} tokens")
    return False

def _codebook_to_text(self, codebook: Dict) -> str:
    """Convert codebook to text for token counting."""
    text_parts = []
    
    for code in codebook.get("codes", []):
        # Include code label and first quote
        text_parts.append(f"Code: {code['label']}")
        
        if code.get("quotes"):
            first_quote = code["quotes"][0]
            text_parts.append(f"Quote: {first_quote['text']}")
    
    return "\n".join(text_parts)
```

### LLMLingua Integration

```python
async def _compress_with_llmlingua(self, codebook: Dict) -> Dict:
    """Compress codebook using LLMLingua."""
    # Convert codebook to documents
    documents = []
    for code in codebook["codes"]:
        doc_text = f"Code ID: {code['code_id']}\n"
        doc_text += f"Label: {code['label']}\n"
        
        # Include at least 1 quote per code
        if code.get("quotes"):
            best_quote = self._select_best_quote(code["quotes"])
            doc_text += f"Quote: {best_quote['text']}"
        
        documents.append(Document(page_content=doc_text))
    
    # Compress using LLMLingua
    compressed_docs = await self.compressor.compress_documents(
        documents,
        query="Generate themes from these codes"
    )
    
    # Convert back to codebook format
    compressed_codebook = self._docs_to_codebook(
        compressed_docs,
        codebook["version"],
        codebook["account_id"]
    )
    
    return compressed_codebook

def _select_best_quote(self, quotes: List[Dict]) -> Dict:
    """Select the best representative quote."""
    # Prefer shorter, clearer quotes
    return min(quotes, key=lambda q: len(q["text"]))
```

### Fallback Compression

```python
def _compress_with_truncation(self, codebook: Dict) -> Dict:
    """Fallback compression using simple truncation."""
    compressed_codes = []
    target_tokens = self.max_tokens_threshold
    current_tokens = 0
    
    for code in codebook["codes"]:
        # Always preserve code ID and label
        compressed_code = {
            "code_id": code["code_id"],
            "label": code["label"],
            "quotes": []
        }
        
        # Add at least 1 quote if available
        if code.get("quotes"):
            best_quote = self._select_best_quote(code["quotes"])
            compressed_code["quotes"] = [best_quote]
        
        # Check if adding this code exceeds token limit
        code_text = self._code_to_text(compressed_code)
        code_tokens = len(self.tokenizer.encode(code_text))
        
        if current_tokens + code_tokens > target_tokens:
            logger.warning(f"Truncation limit reached at {len(compressed_codes)} codes")
            break
        
        compressed_codes.append(compressed_code)
        current_tokens += code_tokens
    
    return {
        "version": codebook["version"],
        "account_id": codebook["account_id"],
        "codes": compressed_codes,
        "created_at": codebook["created_at"],
        "updated_at": codebook["updated_at"]
    }
```

## Theme Generation

### Prompt Templates

```python
THEME_GENERATION_PROMPT = """
Analyze the following codebook and identify 3-8 overarching themes that capture the main patterns and concepts.

For each theme:
1. Provide a concise title (max 200 characters)
2. Write a brief description explaining the theme
3. Select 2-3 representative quotes that best exemplify the theme
4. List the code IDs that support this theme

Codebook:
{codebook_text}

Respond in JSON format:
{{
  "themes": [
    {{
      "title": "Theme title here",
      "description": "Theme description here",
      "quotes": [
        {{
          "quote_id": "quote_id_from_codebook",
          "text": "Quote text",
          "interaction_id": "interaction_uuid"
        }}
      ],
      "code_ids": ["code_uuid_1", "code_uuid_2"]
    }}
  ]
}}
"""

async def _generate_themes_llm(self, codebook: Dict) -> List[Dict]:
    """Generate themes using LLM."""
    codebook_text = self._format_codebook_for_prompt(codebook)
    
    prompt = THEME_GENERATION_PROMPT.format(
        codebook_text=codebook_text
    )
    
    response = await self.openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an expert thematic analyst."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.1  # Low temperature for consistency
    )
    
    return self._parse_themes_response(response.choices[0].message.content)
```

## Error Handling

### Retry Logic

```python
async def _generate_themes_with_retry(self, codebook: Dict) -> List[Dict]:
    """Generate themes with exponential backoff retry."""
    max_retries = 3
    base_delay = 1.0
    
    for attempt in range(max_retries):
        try:
            return await self._generate_themes_llm(codebook)
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Theme generation failed after {max_retries} attempts: {e}")
                return []
            
            delay = base_delay * (2 ** attempt)
            logger.warning(f"Theme generation attempt {attempt + 1} failed, retrying in {delay}s: {e}")
            await asyncio.sleep(delay)
```

### Fallback Handling

```python
async def _compress_codebook(self, codebook: Dict) -> Dict:
    """Compress codebook with automatic fallback."""
    if self.llmlingua_available:
        try:
            compressed = await self._compress_with_llmlingua(codebook)
            logger.info("LLMLingua compression successful")
            return compressed
        except Exception as e:
            logger.warning(f"LLMLingua failed, using fallback: {e}")
            return self._compress_with_truncation(codebook)
    else:
        logger.info("LLMLingua not available, using fallback")
        return self._compress_with_truncation(codebook)
```

## Cost Tracking

```python
def _track_cost(self, response) -> Dict:
    """Track token usage and cost."""
    usage = response.usage
    
    # GPT-4o pricing (example rates)
    prompt_cost_per_token = 0.00001
    completion_cost_per_token = 0.00003
    
    prompt_cost = usage.prompt_tokens * prompt_cost_per_token
    completion_cost = usage.completion_tokens * completion_cost_per_token
    total_cost = prompt_cost + completion_cost
    
    return {
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "total_tokens": usage.total_tokens,
        "estimated_cost_usd": total_cost
    }
```

## Performance Considerations

- **Compression Time**: LLMLingua ~2-5 seconds, truncation ~100ms
- **LLM Generation**: ~5-10 seconds for theme generation
- **Memory Usage**: Compressed codebook uses ~50-70% less memory
- **Token Efficiency**: Compression reduces LLM costs by ~40-60%
