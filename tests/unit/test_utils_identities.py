"""Unit tests for identity loading and validation."""

import pytest
import tempfile
import os
from pathlib import Path

from src.thematic_lm.utils.identities import Identity, load_identities


def test_valid_identities_with_all_fields():
    """Test loading identities with all fields including optional description."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
identities:
  - id: analyst
    name: "Analytical Perspective"
    description: "Focuses on objective analysis"
    prompt_prefix: "You are an analytical researcher..."
  - id: empathetic
    name: "Empathetic Perspective"
    description: "Focuses on emotional understanding"
    prompt_prefix: "You are an empathetic listener..."
""")
        temp_path = f.name
    
    try:
        identities = load_identities(temp_path)
        
        assert len(identities) == 2
        
        assert identities[0].id == "analyst"
        assert identities[0].name == "Analytical Perspective"
        assert identities[0].description == "Focuses on objective analysis"
        assert identities[0].prompt_prefix == "You are an analytical researcher..."
        
        assert identities[1].id == "empathetic"
        assert identities[1].name == "Empathetic Perspective"
        assert identities[1].description == "Focuses on emotional understanding"
        assert identities[1].prompt_prefix == "You are an empathetic listener..."
    finally:
        os.unlink(temp_path)
        # Clear cache for next test
        load_identities.cache_clear()


def test_valid_identities_without_optional_description():
    """Test loading identities without optional description field."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
identities:
  - id: analyst
    name: "Analytical Perspective"
    prompt_prefix: "You are an analytical researcher..."
  - id: empathetic
    name: "Empathetic Perspective"
    prompt_prefix: "You are an empathetic listener..."
""")
        temp_path = f.name
    
    try:
        identities = load_identities(temp_path)
        
        assert len(identities) == 2
        
        assert identities[0].id == "analyst"
        assert identities[0].name == "Analytical Perspective"
        assert identities[0].description is None
        assert identities[0].prompt_prefix == "You are an analytical researcher..."
        
        assert identities[1].id == "empathetic"
        assert identities[1].name == "Empathetic Perspective"
        assert identities[1].description is None
        assert identities[1].prompt_prefix == "You are an empathetic listener..."
    finally:
        os.unlink(temp_path)
        load_identities.cache_clear()


def test_missing_required_field_id():
    """Test that missing 'id' field raises ValueError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
identities:
  - name: "Analytical Perspective"
    prompt_prefix: "You are an analytical researcher..."
""")
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError, match="Identity missing required fields.*id"):
            load_identities(temp_path)
    finally:
        os.unlink(temp_path)
        load_identities.cache_clear()


def test_missing_required_field_name():
    """Test that missing 'name' field raises ValueError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
identities:
  - id: analyst
    prompt_prefix: "You are an analytical researcher..."
""")
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError, match="Identity missing required fields.*name"):
            load_identities(temp_path)
    finally:
        os.unlink(temp_path)
        load_identities.cache_clear()


def test_missing_required_field_prompt_prefix():
    """Test that missing 'prompt_prefix' field raises ValueError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
identities:
  - id: analyst
    name: "Analytical Perspective"
""")
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError, match="Identity missing required fields.*prompt_prefix"):
            load_identities(temp_path)
    finally:
        os.unlink(temp_path)
        load_identities.cache_clear()


def test_missing_file():
    """Test that missing file raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        load_identities("nonexistent_file.yaml")
    
    load_identities.cache_clear()


def test_empty_identities_list():
    """Test that empty identities list raises ValueError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
identities: []
""")
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError, match="No identities defined in identities.yaml"):
            load_identities(temp_path)
    finally:
        os.unlink(temp_path)
        load_identities.cache_clear()


def test_missing_identities_key():
    """Test that missing 'identities' key raises ValueError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
some_other_key:
  - id: analyst
    name: "Analytical Perspective"
    prompt_prefix: "You are an analytical researcher..."
""")
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError, match="No 'identities' key in identities.yaml"):
            load_identities(temp_path)
    finally:
        os.unlink(temp_path)
        load_identities.cache_clear()


def test_cache_verification():
    """Test that identities are cached and multiple calls return same object."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
identities:
  - id: analyst
    name: "Analytical Perspective"
    prompt_prefix: "You are an analytical researcher..."
""")
        temp_path = f.name
    
    try:
        # First call
        identities1 = load_identities(temp_path)
        
        # Second call should return cached result
        identities2 = load_identities(temp_path)
        
        # Verify same object (cached)
        assert identities1 is identities2
        
        # Verify cache info
        cache_info = load_identities.cache_info()
        assert cache_info.hits >= 1
        assert cache_info.misses >= 1
    finally:
        os.unlink(temp_path)
        load_identities.cache_clear()


def test_duplicate_ids_raises_value_error():
    """Test that duplicate identity IDs raise ValueError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
identities:
  - id: analyst
    name: "Analytical Perspective"
    prompt_prefix: "You are an analytical researcher..."
  - id: analyst
    name: "Another Analyst"
    prompt_prefix: "You are another analyst..."
""")
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError, match="Duplicate identity id: analyst"):
            load_identities(temp_path)
    finally:
        os.unlink(temp_path)
        load_identities.cache_clear()


def test_empty_id_raises_value_error():
    """Test that empty id field raises ValueError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
identities:
  - id: ""
    name: "Analytical Perspective"
    prompt_prefix: "You are an analytical researcher..."
""")
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError, match="Identity fields must be non-empty: id"):
            load_identities(temp_path)
    finally:
        os.unlink(temp_path)
        load_identities.cache_clear()


def test_whitespace_id_raises_value_error():
    """Test that whitespace-only id field raises ValueError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
identities:
  - id: "   "
    name: "Analytical Perspective"
    prompt_prefix: "You are an analytical researcher..."
""")
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError, match="Identity fields must be non-empty: id"):
            load_identities(temp_path)
    finally:
        os.unlink(temp_path)
        load_identities.cache_clear()


def test_empty_name_raises_value_error():
    """Test that empty name field raises ValueError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
identities:
  - id: analyst
    name: ""
    prompt_prefix: "You are an analytical researcher..."
""")
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError, match="Identity fields must be non-empty: name"):
            load_identities(temp_path)
    finally:
        os.unlink(temp_path)
        load_identities.cache_clear()


def test_whitespace_name_raises_value_error():
    """Test that whitespace-only name field raises ValueError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
identities:
  - id: analyst
    name: "   "
    prompt_prefix: "You are an analytical researcher..."
""")
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError, match="Identity fields must be non-empty: name"):
            load_identities(temp_path)
    finally:
        os.unlink(temp_path)
        load_identities.cache_clear()


def test_empty_prompt_prefix_raises_value_error():
    """Test that empty prompt_prefix field raises ValueError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
identities:
  - id: analyst
    name: "Analytical Perspective"
    prompt_prefix: ""
""")
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError, match="Identity fields must be non-empty: prompt_prefix"):
            load_identities(temp_path)
    finally:
        os.unlink(temp_path)
        load_identities.cache_clear()


def test_whitespace_prompt_prefix_raises_value_error():
    """Test that whitespace-only prompt_prefix field raises ValueError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
identities:
  - id: analyst
    name: "Analytical Perspective"
    prompt_prefix: "   "
""")
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError, match="Identity fields must be non-empty: prompt_prefix"):
            load_identities(temp_path)
    finally:
        os.unlink(temp_path)
        load_identities.cache_clear()


def test_invalid_yaml_empty_string():
    """Test that empty YAML string raises ValueError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("")
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError, match="Invalid identities.yaml format"):
            load_identities(temp_path)
    finally:
        os.unlink(temp_path)
        load_identities.cache_clear()


def test_invalid_yaml_list():
    """Test that YAML list (not dict) raises ValueError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
- id: analyst
  name: "Analytical Perspective"
  prompt_prefix: "You are an analytical researcher..."
""")
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError, match="Invalid identities.yaml format"):
            load_identities(temp_path)
    finally:
        os.unlink(temp_path)
        load_identities.cache_clear()


def test_invalid_yaml_scalar():
    """Test that YAML scalar (not dict) raises ValueError."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("42")
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError, match="Invalid identities.yaml format"):
            load_identities(temp_path)
    finally:
        os.unlink(temp_path)
        load_identities.cache_clear()
