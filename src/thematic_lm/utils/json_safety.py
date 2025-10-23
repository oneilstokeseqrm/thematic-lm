"""Safe JSON parsing utilities with fallback strategies."""

import json
import re
from typing import Any, Dict, List

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
    
    # Strategy 4: Extract first JSON array using regex
    # Try to find array boundaries and parse incrementally
    start_idx = content.find('[')
    if start_idx != -1:
        # Try to parse from each potential end position
        bracket_count = 0
        in_string = False
        escape_next = False
        
        for i in range(start_idx, len(content)):
            char = content[i]
            
            if escape_next:
                escape_next = False
                continue
            
            if char == '\\':
                escape_next = True
                continue
            
            if char == '"' and not escape_next:
                in_string = not in_string
                continue
            
            if not in_string:
                if char == '[':
                    bracket_count += 1
                elif char == ']':
                    bracket_count -= 1
                    if bracket_count == 0:
                        # Found matching closing bracket
                        try:
                            result = json.loads(content[start_idx:i+1])
                            if isinstance(result, list):
                                return result
                        except json.JSONDecodeError:
                            pass
                        break
    
    logger.warning("Failed to parse JSON from LLM output", content_length=len(content))
    return []
