#!/usr/bin/env python3
"""
Contract Validation Script

Validates:
1. All JSON schemas are valid against JSON Schema meta-schema (draft-07)
2. All examples validate against their corresponding schemas
3. Quote IDs in examples match canonical regex pattern
4. All UUIDs are valid format
5. All timestamps are valid ISO 8601

Usage:
    python scripts/validate_contracts.py
    python scripts/validate_contracts.py --contract events/analysis-events/v1

Exit code 0 = all valid, 1 = validation errors
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Tuple
from datetime import datetime

try:
    import jsonschema
    from jsonschema import Draft7Validator
except ImportError:
    print("Error: jsonschema package not installed")
    print("Install with: pip install jsonschema")
    sys.exit(1)

# Canonical quote ID regex pattern
QUOTE_ID_PATTERN = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}:'
    r'(msg_\d+:)?ch_\d+:\d+-\d+$'
)

# UUID regex pattern
UUID_PATTERN = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
)


def validate_schema(schema_path: Path) -> List[str]:
    """Validate a JSON schema against meta-schema."""
    errors = []
    
    try:
        with open(schema_path) as f:
            schema = json.load(f)
    except json.JSONDecodeError as e:
        return [f"Invalid JSON in {schema_path}: {e}"]
    except Exception as e:
        return [f"Error reading {schema_path}: {e}"]
    
    # Check required fields
    if '$schema' not in schema:
        errors.append(f"{schema_path}: Missing $schema field")
    elif schema['$schema'] != "http://json-schema.org/draft-07/schema#":
        errors.append(f"{schema_path}: $schema must be draft-07")
    
    if '$id' not in schema:
        errors.append(f"{schema_path}: Missing $id field")
    
    # Validate against meta-schema
    try:
        Draft7Validator.check_schema(schema)
    except jsonschema.SchemaError as e:
        errors.append(f"{schema_path}: Invalid schema: {e.message}")
    
    return errors


def validate_example(example_path: Path, schema_path: Path) -> List[str]:
    """Validate an example against its schema."""
    errors = []
    
    try:
        with open(example_path) as f:
            example = json.load(f)
    except json.JSONDecodeError as e:
        return [f"Invalid JSON in {example_path}: {e}"]
    except Exception as e:
        return [f"Error reading {example_path}: {e}"]
    
    try:
        with open(schema_path) as f:
            schema = json.load(f)
    except Exception as e:
        return [f"Error reading schema {schema_path}: {e}"]
    
    # Validate example against schema
    try:
        validator = Draft7Validator(schema)
        validation_errors = list(validator.iter_errors(example))
        for error in validation_errors:
            path = ".".join(str(p) for p in error.path)
            errors.append(
                f"{example_path}: Validation error at {path}: {error.message}"
            )
    except Exception as e:
        errors.append(f"{example_path}: Validation failed: {e}")
    
    return errors


def validate_quote_ids(data: dict, path: str = "") -> List[str]:
    """Recursively validate quote IDs in data structure."""
    errors = []
    
    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            
            if key == "quote_id" and isinstance(value, str):
                if not QUOTE_ID_PATTERN.match(value):
                    errors.append(
                        f"{current_path}: Invalid quote ID format: {value}"
                    )
            else:
                errors.extend(validate_quote_ids(value, current_path))
    
    elif isinstance(data, list):
        for i, item in enumerate(data):
            current_path = f"{path}[{i}]"
            errors.extend(validate_quote_ids(item, current_path))
    
    return errors


def validate_uuids(data: dict, path: str = "") -> List[str]:
    """Recursively validate UUIDs in data structure."""
    errors = []
    
    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            
            # Check fields that should be UUIDs (but not quote_id which has special format)
            if key.endswith("_id") and key != "quote_id" and isinstance(value, str):
                if not UUID_PATTERN.match(value.lower()):
                    errors.append(
                        f"{current_path}: Invalid UUID format: {value}"
                    )
            else:
                errors.extend(validate_uuids(value, current_path))
    
    elif isinstance(data, list):
        for i, item in enumerate(data):
            current_path = f"{path}[{i}]"
            errors.extend(validate_uuids(item, current_path))
    
    return errors


def validate_timestamps(data: dict, path: str = "") -> List[str]:
    """Recursively validate ISO 8601 timestamps in data structure."""
    errors = []
    
    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{path}.{key}" if path else key
            
            # Check fields that should be timestamps
            if (key.endswith("_at") or key == "timestamp") and isinstance(value, str):
                try:
                    datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    errors.append(
                        f"{current_path}: Invalid ISO 8601 timestamp: {value}"
                    )
            else:
                errors.extend(validate_timestamps(value, current_path))
    
    elif isinstance(data, list):
        for i, item in enumerate(data):
            current_path = f"{path}[{i}]"
            errors.extend(validate_timestamps(item, current_path))
    
    return errors


def validate_contract(contract_path: Path) -> Tuple[int, int]:
    """Validate a single contract (schema + examples)."""
    errors = []
    total_checks = 0
    
    schema_path = contract_path / "schema.json"
    examples_dir = contract_path / "examples"
    
    # Validate schema if it exists
    if schema_path.exists():
        total_checks += 1
        schema_errors = validate_schema(schema_path)
        if schema_errors:
            errors.extend(schema_errors)
        else:
            print(f"✓ Schema valid: {schema_path}")
    
    # Validate examples if they exist
    if examples_dir.exists() and schema_path.exists():
        for example_file in examples_dir.glob("*.json"):
            total_checks += 1
            
            # Validate against schema
            example_errors = validate_example(example_file, schema_path)
            if example_errors:
                errors.extend(example_errors)
            else:
                print(f"✓ Example valid: {example_file}")
            
            # Validate quote IDs, UUIDs, and timestamps
            try:
                with open(example_file) as f:
                    example_data = json.load(f)
                
                quote_id_errors = validate_quote_ids(example_data)
                if quote_id_errors:
                    errors.extend([f"{example_file}: {e}" for e in quote_id_errors])
                
                uuid_errors = validate_uuids(example_data)
                if uuid_errors:
                    errors.extend([f"{example_file}: {e}" for e in uuid_errors])
                
                timestamp_errors = validate_timestamps(example_data)
                if timestamp_errors:
                    errors.extend([f"{example_file}: {e}" for e in timestamp_errors])
            
            except Exception as e:
                errors.append(f"{example_file}: Error validating content: {e}")
    
    # Print errors
    if errors:
        print(f"\n✗ Validation errors in {contract_path}:")
        for error in errors:
            print(f"  - {error}")
    
    return total_checks, len(errors)


def main():
    parser = argparse.ArgumentParser(description="Validate contract schemas and examples")
    parser.add_argument(
        "--contract",
        help="Specific contract to validate (e.g., events/analysis-events/v1)"
    )
    args = parser.parse_args()
    
    contracts_dir = Path(".kiro/contracts")
    
    if not contracts_dir.exists():
        print(f"Error: Contracts directory not found: {contracts_dir}")
        sys.exit(1)
    
    total_checks = 0
    total_errors = 0
    
    if args.contract:
        # Validate specific contract
        contract_path = contracts_dir / args.contract
        if not contract_path.exists():
            print(f"Error: Contract not found: {contract_path}")
            sys.exit(1)
        
        checks, errors = validate_contract(contract_path)
        total_checks += checks
        total_errors += errors
    else:
        # Validate all contracts
        print("Validating all contracts...\n")
        
        # Find all v* directories (versioned contracts)
        for version_dir in contracts_dir.rglob("v*"):
            if version_dir.is_dir() and version_dir.name.startswith("v"):
                checks, errors = validate_contract(version_dir)
                total_checks += checks
                total_errors += errors
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Total checks: {total_checks}")
    print(f"Total errors: {total_errors}")
    
    if total_errors == 0:
        print("✓ All contracts valid!")
        sys.exit(0)
    else:
        print(f"✗ {total_errors} validation error(s) found")
        sys.exit(1)


if __name__ == "__main__":
    main()
