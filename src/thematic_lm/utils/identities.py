"""Identity loading and validation for coder agents."""

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
        ValueError: If required fields missing, empty, duplicate IDs, or invalid YAML format
    """
    with open(path) as f:
        config = yaml.safe_load(f)
    
    # Guard against invalid YAML structure
    if config is None or not isinstance(config, dict):
        raise ValueError("Invalid identities.yaml format")
    
    if "identities" not in config:
        raise ValueError("No 'identities' key in identities.yaml")
    
    identities = []
    required_fields = ["id", "name", "prompt_prefix"]
    seen_ids = set()
    
    for item in config["identities"]:
        # Check for missing fields
        missing = [k for k in required_fields if k not in item]
        if missing:
            raise ValueError(f"Identity missing required fields {missing}: {item}")
        
        # Validate non-empty strings for required fields
        for field in required_fields:
            value = item[field]
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Identity fields must be non-empty: {field}")
        
        # Check for duplicate IDs
        identity_id = item["id"].strip()
        if identity_id in seen_ids:
            raise ValueError(f"Duplicate identity id: {identity_id}")
        seen_ids.add(identity_id)
        
        # Strip whitespace from required fields
        item["id"] = item["id"].strip()
        item["name"] = item["name"].strip()
        item["prompt_prefix"] = item["prompt_prefix"].strip()
        
        # Strip description if present
        if "description" in item and item["description"]:
            item["description"] = item["description"].strip()
        
        identities.append(Identity(**item))
    
    if not identities:
        raise ValueError("No identities defined in identities.yaml")
    
    return identities
