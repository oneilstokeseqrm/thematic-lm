"""Tests for safe JSON parsing utilities."""

import json
from unittest.mock import patch

import pytest

from thematic_lm.utils.json_safety import parse_json_array


class TestParseJsonArray:
    """Test parse_json_array with various input formats."""
    
    def test_direct_json_array_parsing(self):
        """Test direct JSON array parsing (Strategy 1)."""
        content = json.dumps([
            {"label": "Code 1", "quotes": []},
            {"label": "Code 2", "quotes": []}
        ])
        
        result = parse_json_array(content)
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["label"] == "Code 1"
        assert result[1]["label"] == "Code 2"
    
    def test_json_with_json_fences(self):
        """Test JSON extraction from ```json fenced block (Strategy 2)."""
        content = """Here is the analysis:

```json
[
  {"label": "Theme A", "quotes": []},
  {"label": "Theme B", "quotes": []}
]
```

That's the result."""
        
        result = parse_json_array(content)
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["label"] == "Theme A"
        assert result[1]["label"] == "Theme B"
    
    def test_json_with_bare_fences(self):
        """Test JSON extraction from bare ``` fenced block (Strategy 3)."""
        content = """Analysis complete:

```
[
  {"label": "Code X", "quotes": []},
  {"label": "Code Y", "quotes": []}
]
```

Done."""
        
        result = parse_json_array(content)
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["label"] == "Code X"
        assert result[1]["label"] == "Code Y"
    
    def test_json_with_trailing_prose(self):
        """Test JSON extraction with trailing prose (Strategy 4)."""
        content = """[
  {"label": "First", "quotes": []},
  {"label": "Second", "quotes": []}
]

This is some additional explanation that comes after the JSON."""
        
        result = parse_json_array(content)
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["label"] == "First"
        assert result[1]["label"] == "Second"
    
    @patch('thematic_lm.utils.json_safety.logger')
    def test_dict_with_codes_key_normalization(self, mock_logger):
        """Test dict with 'codes' key normalization and WARNING log."""
        content = json.dumps({
            "codes": [
                {"label": "Code A", "quotes": []},
                {"label": "Code B", "quotes": []}
            ]
        })
        
        result = parse_json_array(content)
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["label"] == "Code A"
        assert result[1]["label"] == "Code B"
        
        # Verify WARNING was logged
        mock_logger.warning.assert_called_once_with(
            "LLM returned dict with 'codes' key; normalizing to array"
        )
    
    @patch('thematic_lm.utils.json_safety.logger')
    def test_malformed_json_returns_empty_list(self, mock_logger):
        """Test malformed JSON returns empty list and logs warning."""
        content = "This is not valid JSON at all {broken: syntax"
        
        result = parse_json_array(content)
        
        assert isinstance(result, list)
        assert len(result) == 0
        
        # Verify WARNING was logged with content_length (no content at INFO)
        mock_logger.warning.assert_called_once_with(
            "Failed to parse JSON from LLM output",
            content_length=len(content)
        )
    
    def test_empty_string_returns_empty_list(self):
        """Test empty string returns empty list."""
        result = parse_json_array("")
        
        assert isinstance(result, list)
        assert len(result) == 0
    
    def test_json_fenced_with_extra_whitespace(self):
        """Test JSON fenced block with extra whitespace."""
        content = """
        
```json

[{"label": "Test", "quotes": []}]

```
        
        """
        
        result = parse_json_array(content)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["label"] == "Test"
    
    def test_nested_json_arrays(self):
        """Test parsing with nested arrays."""
        content = json.dumps([
            {"label": "Code 1", "quotes": [{"text": "quote1"}]},
            {"label": "Code 2", "quotes": [{"text": "quote2"}, {"text": "quote3"}]}
        ])
        
        result = parse_json_array(content)
        
        assert isinstance(result, list)
        assert len(result) == 2
        assert len(result[0]["quotes"]) == 1
        assert len(result[1]["quotes"]) == 2
    
    @patch('thematic_lm.utils.json_safety.logger')
    def test_dict_with_codes_key_in_fenced_block(self, mock_logger):
        """Test dict with 'codes' key inside fenced block."""
        content = """```json
{
  "codes": [
    {"label": "Fenced Code", "quotes": []}
  ]
}
```"""
        
        result = parse_json_array(content)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["label"] == "Fenced Code"
        
        # Verify WARNING was logged
        mock_logger.warning.assert_called_once_with(
            "LLM returned dict with 'codes' key; normalizing to array"
        )
    
    def test_multiple_json_arrays_extracts_first(self):
        """Test that regex strategy extracts first JSON array."""
        content = """First array: [{"label": "First"}]
        
Second array: [{"label": "Second"}]"""
        
        result = parse_json_array(content)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["label"] == "First"
