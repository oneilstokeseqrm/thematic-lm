# Design: Code Aggregator

## Architecture Overview

The code aggregator deduplicates and merges codes from multiple coder agents while preserving all quotes. It uses fuzzy string matching to identify similar codes and consolidates them into a unified code list.

## Key Classes/Functions

### CodeAggregator

```python
from typing import List, Dict
from difflib import SequenceMatcher

class CodeAggregator:
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
    
    def aggregate_codes(self, coder_outputs: List[List[Dict]]) -> List[Dict]:
        """Aggregate codes from multiple coder agents."""
        # Flatten all codes from all agents
        all_codes = []
        for agent_codes in coder_outputs:
            all_codes.extend(agent_codes)
        
        # Deduplicate and merge
        merged_codes = self._merge_similar_codes(all_codes)
        
        return merged_codes
    
    def _merge_similar_codes(self, codes: List[Dict]) -> List[Dict]:
        """Merge codes with similar labels."""
        merged = []
        used_indices = set()
        
        for i, code in enumerate(codes):
            if i in used_indices:
                continue
            
            # Find all similar codes
            similar_codes = [code]
            for j, other_code in enumerate(codes[i+1:], start=i+1):
                if j in used_indices:
                    continue
                
                if self._are_similar(code["label"], other_code["label"]):
                    similar_codes.append(other_code)
                    used_indices.add(j)
            
            # Merge similar codes
            merged_code = self._merge_code_group(similar_codes)
            merged.append(merged_code)
            used_indices.add(i)
        
        return merged
    
    def _are_similar(self, label1: str, label2: str) -> bool:
        """Check if two labels are similar using fuzzy matching."""
        similarity = SequenceMatcher(None, label1.lower(), label2.lower()).ratio()
        return similarity >= self.similarity_threshold
    
    def _merge_code_group(self, codes: List[Dict]) -> Dict:
        """Merge a group of similar codes."""
        # Select most descriptive label (longest)
        best_label = max(codes, key=lambda c: len(c["label"]))["label"]
        
        # Combine all quotes, deduplicate by quote_id
        all_quotes = []
        seen_quote_ids = set()
        
        for code in codes:
            for quote in code.get("quotes", []):
                quote_id = quote["quote_id"]
                if quote_id not in seen_quote_ids:
                    all_quotes.append(quote)
                    seen_quote_ids.add(quote_id)
        
        return {
            "label": best_label,
            "quotes": all_quotes
        }
```

## Merging Strategy

### Similarity Detection

1. **Exact Match**: Labels are identical (case-insensitive)
2. **Fuzzy Match**: SequenceMatcher ratio ≥ 0.85
3. **Keep Separate**: Ratio < 0.85

### Label Selection

When merging codes, select the most descriptive label:
- Prefer longer labels (more detail)
- Preserve original wording (no rewriting)

### Quote Preservation

- Combine quotes arrays from all merged codes
- Deduplicate by `quote_id` (exact match)
- Maintain quote order (chronological by interaction)

## Dependencies

- **internal/agents-coder@v1**: Receives code outputs from coder agents
- No external API dependencies (pure logic)

## Error Handling

- **Empty Codes List**: Return empty list (valid case)
- **Missing Quotes**: Log warning, keep code with empty quotes array
- **Invalid Quote ID**: Log warning, skip quote
- **Duplicate Labels**: Merge automatically (expected behavior)

## Performance Considerations

- **O(n²) Complexity**: Pairwise comparison of all codes
- **Optimization**: Early termination when similarity found
- **Typical Scale**: 10-100 codes per analysis (acceptable performance)
