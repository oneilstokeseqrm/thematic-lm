# Design: Identity-Based Coder Agents

## Architecture Overview

Coder agents are LLM-powered agents that analyze interactions and generate descriptive codes with supporting quotes. Each agent operates with a specific identity perspective (loaded from identities.yaml) to capture diverse interpretations.

## Key Classes/Functions

### CoderAgent

```python
class CoderAgent:
    def __init__(self, identity: Identity, llm_client: OpenAIClient):
        self.identity = identity
        self.llm_client = llm_client
    
    async def code_interaction(
        self,
        interaction: Dict,
        chunks: List[Dict]
    ) -> List[Code]:
        """Generate codes for an interaction."""
        codes = []
        
        for chunk in chunks:
            chunk_codes = await self._code_chunk(chunk, interaction["id"])
            codes.extend(chunk_codes)
        
        return codes
    
    async def _code_chunk(self, chunk: Dict, interaction_id: str) -> List[Code]:
        """Generate codes for a single chunk."""
        prompt = self._build_prompt(chunk["text"])
        response = await self.llm_client.chat_completion(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": self.identity.prompt_prefix},
                {"role": "user", "content": prompt}
            ]
        )
        
        return self._parse_response(response, chunk, interaction_id)
```

### Prompt Template

```python
CODER_PROMPT_TEMPLATE = """
Analyze the following text and generate 1-3 descriptive codes that capture key themes or concepts.

For each code:
1. Provide a concise label (max 200 characters)
2. Extract a representative quote from the text that supports the code
3. Ensure the quote is verbatim from the text

Text to analyze:
{text}

Respond in JSON format:
{{
  "codes": [
    {{
      "label": "Code label here",
      "quote": "Exact quote from text"
    }}
  ]
}}
"""
```

### Quote ID Encoding

```python
def encode_quote_id(
    interaction_id: str,
    chunk_index: int,
    start_pos: int,
    end_pos: int
) -> str:
    """Encode quote ID per models/quote_id@v1."""
    return f"{interaction_id}:ch_{chunk_index}:{start_pos}-{end_pos}"

def find_quote_position(text: str, quote: str) -> Tuple[int, int]:
    """Find Unicode code-point positions of quote in text."""
    start_pos = text.find(quote)
    if start_pos == -1:
        raise ValueError(f"Quote not found in text: {quote}")
    
    end_pos = start_pos + len(quote)
    return start_pos, end_pos
```

## Dependencies

- **models/chunking@v1**: Receives chunked interactions
- **models/quote_id@v1**: Encodes quote IDs
- **internal/cost-management@v1**: Tracks token usage

## External API Integrations

- **OpenAI GPT-4o**: Code generation
- **Rate Limiting**: Via cost-manager component
- **Retry Strategy**: Exponential backoff (max 3 retries)

## Error Handling

- **LLM API Failure**: Retry up to 3 times, then fail
- **Quote Not Found**: Log warning, skip code
- **Invalid JSON Response**: Log error, retry once
- **Cost Budget Exceeded**: Abort immediately
