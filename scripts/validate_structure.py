#!/usr/bin/env python3
"""Validate Phase A project structure."""

import os
import sys
from pathlib import Path

# Expected files and directories
EXPECTED_STRUCTURE = {
    "files": [
        "pyproject.toml",
        ".env.example",
        "identities.yaml",
        "alembic.ini",
        "README.md",
        "PHASE_A_COMPLETE.md",
        # Source files
        "src/thematic_lm/__init__.py",
        "src/thematic_lm/config/__init__.py",
        "src/thematic_lm/config/settings.py",
        "src/thematic_lm/utils/__init__.py",
        "src/thematic_lm/utils/logging.py",
        "src/thematic_lm/models/__init__.py",
        "src/thematic_lm/models/database.py",
        "src/thematic_lm/api/__init__.py",
        "src/thematic_lm/api/main.py",
        "src/thematic_lm/api/middleware.py",
        "src/thematic_lm/api/routes.py",
        "src/thematic_lm/api/dependencies.py",
        "src/thematic_lm/orchestrator/__init__.py",
        "src/thematic_lm/orchestrator/state.py",
        "src/thematic_lm/orchestrator/nodes.py",
        "src/thematic_lm/orchestrator/graph.py",
        # Tests
        "tests/__init__.py",
        "tests/conftest.py",
        "tests/unit/__init__.py",
        "tests/unit/test_config.py",
        "tests/unit/test_api.py",
        "tests/integration/__init__.py",
        "tests/integration/test_database.py",
        # Alembic
        "alembic/env.py",
        "alembic/script.py.mako",
        "alembic/versions/001_initial_schema.py",
        # Scripts
        "scripts/setup_dev.sh",
        "scripts/validate_contracts.py",
    ],
    "directories": [
        "src/thematic_lm",
        "src/thematic_lm/config",
        "src/thematic_lm/utils",
        "src/thematic_lm/models",
        "src/thematic_lm/api",
        "src/thematic_lm/orchestrator",
        "tests",
        "tests/unit",
        "tests/integration",
        "alembic",
        "alembic/versions",
        "scripts",
    ],
}


def validate_structure() -> bool:
    """Validate that all expected files and directories exist.

    Returns:
        True if all files exist, False otherwise
    """
    root = Path.cwd()
    all_valid = True

    print("Validating Phase A project structure...\n")

    # Check directories
    print("Checking directories:")
    for directory in EXPECTED_STRUCTURE["directories"]:
        path = root / directory
        if path.is_dir():
            print(f"  ✅ {directory}")
        else:
            print(f"  ❌ {directory} (missing)")
            all_valid = False

    print("\nChecking files:")
    for file in EXPECTED_STRUCTURE["files"]:
        path = root / file
        if path.is_file():
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} (missing)")
            all_valid = False

    print("\n" + "=" * 60)
    if all_valid:
        print("✅ All Phase A files and directories are present!")
        print("\nNext steps:")
        print("  1. Run: ./scripts/setup_dev.sh")
        print("  2. Configure .env with your API keys")
        print("  3. Start API: uvicorn src.thematic_lm.api.main:app --reload")
        return True
    else:
        print("❌ Some files or directories are missing")
        return False


if __name__ == "__main__":
    success = validate_structure()
    sys.exit(0 if success else 1)
