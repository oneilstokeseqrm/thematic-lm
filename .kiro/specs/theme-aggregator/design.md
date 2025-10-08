# Design: Theme Aggregator

## Architecture Overview

The theme aggregator merges and curates final themes from multiple theme coder agents. It uses semantic similarity to deduplicate themes, consolidates quotes, and applies quality thresholds to produce high-quality final themes.

```
┌─────────────────────────────────────────────────────────────┐
│                 Theme Aggregator                             │
│  ┌────────────────────────────────────────────────────┐    │
│  │           Aggregation Pipeline                      │    │
│  │                                                      │    │
│  │  [Theme Proposals] → [Merge Similar] → [Quality]   │    │
│  │                           ↓               ↓         │    │
│  │                  [Consolidate Quotes] → [Validate]  │    │
│  │                           ↓                          │    │
│  │                  [Final Themes Output]               │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  Semantic Similarity ←→ SequenceMatcher                     │
│  Quote Selection ←→ Diversity + Clarity                     │
│  Quality Thresholds ←→ Configurable MIN_INTERACTIONS        │
└─────────────────────────────────────────────────────────────┘
```

## Key Classes/Functions

### ThemeAggregator

```python
from typing import List, Dict, Set
from difflib import SequenceMatcher
from collections import defaultdict
import re
import uuid
from datetime import datetime

class ThemeAggregator:
    def __init__(
        self,
        similarity_threshold: float = 0.80,
        min_interactions_per_theme: int = 3,
        max_quotes_per_theme: int = 5
    ):
        self.similarity_threshold = similarity_threshold
        self.min_interactions_per_theme = min_interactions_per_theme
        self.max_quotes_per_theme = max_quotes_per_theme
    
    def aggregate_themes(
        self,
        theme_proposals: List[List[Dict]],
        analysis_id: str,
        account_id: str,
        codebook_version: str
    ) -> Dict:
        """Aggregate themes from multiple theme coder agents."""
        # Flatten all themes from all agents
        all_themes = []
        for agent_themes in theme_proposals:
            all_themes.extend(agent_themes)
        
        # Merge similar themes
        merged_themes = self._merge_similar_themes(all_themes)
        
        # Apply quality thresholds
        quality_themes = self._apply_quality_thresholds(merged_themes)
        
        # Consolidate quotes
        final_themes = self._consolidate_quotes(quality_themes)
        
        # Create final output structure
        return self._create_themes_output(
            final_themes,
            analysis_id,
            account_id,
            codebook_version
        )
```

## Merging Strategy

### Semantic Similarity Detection

```python
def _are_themes_similar(self, theme1: Dict, theme2: Dict) -> bool:
    """Check if two themes are similar using title and description."""
    # Compare titles
    title_similarity = SequenceMatcher(
        None,
        theme1["title"].lower(),
        theme2["title"].lower()
    ).ratio()
    
    # Compare descriptions
    desc_similarity = SequenceMatcher(
        None,
        theme1["description"].lower(),
        theme2["description"].lower()
    ).ratio()
    
    # Use weighted average (title more important)
    combined_similarity = (title_similarity * 0.7) + (desc_similarity * 0.3)
    
    return combined_similarity >= self.similarity_threshold

def _merge_similar_themes(self, themes: List[Dict]) -> List[Dict]:
    """Merge themes with similar content."""
    merged = []
    used_indices = set()
    
    for i, theme in enumerate(themes):
        if i in used_indices:
            continue
        
        # Find all similar themes
        similar_themes = [theme]
        for j, other_theme in enumerate(themes[i+1:], start=i+1):
            if j in used_indices:
                continue
            
            if self._are_themes_similar(theme, other_theme):
                similar_themes.append(other_theme)
                used_indices.add(j)
        
        # Merge similar themes
        merged_theme = self._merge_theme_group(similar_themes)
        merged.append(merged_theme)
        used_indices.add(i)
    
    return merged

def _merge_theme_group(self, themes: List[Dict]) -> Dict:
    """Merge a group of similar themes."""
    # Select best title (most descriptive)
    best_title = max(themes, key=lambda t: len(t["title"]))["title"]
    
    # Select best description (most detailed)
    best_description = max(themes, key=lambda t: len(t["description"]))["description"]
    
    # Combine all quotes and code_ids
    all_quotes = []
    all_code_ids = set()
    
    for theme in themes:
        all_quotes.extend(theme.get("quotes", []))
        all_code_ids.update(theme.get("code_ids", []))
    
    return {
        "title": best_title,
        "description": best_description,
        "quotes": all_quotes,
        "code_ids": list(all_code_ids)
    }
```

## Quote Consolidation

```python
def _consolidate_quotes(self, themes: List[Dict]) -> List[Dict]:
    """Consolidate and optimize quotes for each theme."""
    consolidated_themes = []
    
    for theme in themes:
        # Deduplicate quotes by quote_id
        unique_quotes = self._deduplicate_quotes(theme["quotes"])
        
        # Select best representative quotes
        selected_quotes = self._select_best_quotes(
            unique_quotes,
            self.max_quotes_per_theme
        )
        
        consolidated_theme = {
            **theme,
            "quotes": selected_quotes
        }
        
        consolidated_themes.append(consolidated_theme)
    
    return consolidated_themes

def _deduplicate_quotes(self, quotes: List[Dict]) -> List[Dict]:
    """Remove duplicate quotes by quote_id."""
    seen_quote_ids = set()
    unique_quotes = []
    
    for quote in quotes:
        quote_id = quote.get("quote_id")
        if quote_id and quote_id not in seen_quote_ids:
            unique_quotes.append(quote)
            seen_quote_ids.add(quote_id)
    
    return unique_quotes

def _select_best_quotes(
    self,
    quotes: List[Dict],
    max_quotes: int
) -> List[Dict]:
    """Select the most representative quotes."""
    if len(quotes) <= max_quotes:
        return quotes
    
    # Group quotes by interaction to ensure diversity
    quotes_by_interaction = defaultdict(list)
    for quote in quotes:
        interaction_id = quote.get("interaction_id")
        quotes_by_interaction[interaction_id].append(quote)
    
    # Select one quote per interaction, up to max_quotes
    selected_quotes = []
    for interaction_quotes in quotes_by_interaction.values():
        if len(selected_quotes) >= max_quotes:
            break
        
        # Select shortest quote from this interaction (clearest)
        best_quote = min(interaction_quotes, key=lambda q: len(q.get("text", "")))
        selected_quotes.append(best_quote)
    
    return selected_quotes[:max_quotes]
```

## Quality Validation

```python
def _apply_quality_thresholds(self, themes: List[Dict]) -> List[Dict]:
    """Apply quality thresholds to filter themes."""
    quality_themes = []
    
    for theme in themes:
        if self._meets_quality_threshold(theme):
            quality_themes.append(theme)
        else:
            logger.warning(f"Theme excluded due to quality: {theme.get('title', 'Unknown')}")
    
    return quality_themes

def _meets_quality_threshold(self, theme: Dict) -> bool:
    """Check if theme meets quality requirements."""
    # Check minimum interactions
    unique_interactions = self._count_unique_interactions(theme["quotes"])
    if unique_interactions < self.min_interactions_per_theme:
        return False
    
    # Check title quality
    title = theme.get("title", "")
    if not title or self._is_generic_title(title):
        return False
    
    # Check description quality
    description = theme.get("description", "")
    if not description or len(description.strip()) < 10:
        return False
    
    return True

def _count_unique_interactions(self, quotes: List[Dict]) -> int:
    """Count unique interactions represented in quotes."""
    interaction_ids = set()
    for quote in quotes:
        interaction_id = quote.get("interaction_id")
        if interaction_id:
            interaction_ids.add(interaction_id)
    
    return len(interaction_ids)

def _is_generic_title(self, title: str) -> bool:
    """Check if title is too generic."""
    generic_patterns = [
        r"^theme \d+$",
        r"^topic \d+$",
        r"^category \d+$",
        r"^general",
        r"^misc"
    ]
    
    title_lower = title.lower().strip()
    
    for pattern in generic_patterns:
        if re.match(pattern, title_lower):
            return True
    
    return False
```

## Output Structure Creation

```python
def _create_themes_output(
    self,
    themes: List[Dict],
    analysis_id: str,
    account_id: str,
    codebook_version: str
) -> Dict:
    """Create final themes output matching models/themes@v1."""
    # Add theme_ids to each theme
    themes_with_ids = []
    for theme in themes:
        theme_with_id = {
            "theme_id": str(uuid.uuid4()),
            **theme
        }
        themes_with_ids.append(theme_with_id)
    
    output = {
        "analysis_id": analysis_id,
        "account_id": account_id,
        "codebook_version": codebook_version,
        "themes": themes_with_ids,
        "created_at": datetime.now().isoformat() + "Z"
    }
    
    # Validate against schema
    self._validate_output(output)
    
    return output

def _validate_output(self, output: Dict) -> None:
    """Validate output against models/themes@v1 contract."""
    required_fields = ["analysis_id", "account_id", "codebook_version", "themes", "created_at"]
    
    for field in required_fields:
        if field not in output:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate each theme
    for theme in output["themes"]:
        theme_required = ["theme_id", "title", "description", "quotes", "code_ids"]
        for field in theme_required:
            if field not in theme:
                raise ValueError(f"Theme missing required field: {field}")
        
        # Validate quotes structure
        for quote in theme["quotes"]:
            quote_required = ["quote_id", "text", "interaction_id"]
            for field in quote_required:
                if field not in quote:
                    raise ValueError(f"Quote missing required field: {field}")
```

## Error Handling

- **Empty Theme Proposals**: Return empty themes array (valid case)
- **Invalid Theme Structure**: Skip malformed themes, log warnings
- **Quality Threshold Failures**: Exclude low-quality themes, log details
- **Validation Failures**: Log detailed errors, attempt to fix common issues
- **Missing Codebook Version**: Log error but continue with theme creation

## Performance Considerations

- **Typical Scale**: 10-50 input themes from multiple agents
- **Merging Complexity**: O(n²) worst case, but n is small (<50)
- **Quote Selection**: O(n log n) for sorting by interaction diversity
- **Processing Time**: <2 seconds for typical workloads
- **Memory Usage**: Minimal (all data fits in memory)
