# Import Path Fixes

## Changes Made

Fixed all import paths in test files to use `src.thematic_lm` prefix instead of `thematic_lm`.

### Files Updated

1. **tests/conftest.py**
   - Changed: `from thematic_lm.models.database import get_db_session`
   - To: `from src.thematic_lm.models.database import get_db_session`

2. **tests/unit/test_config.py**
   - Changed: `from thematic_lm.config import Settings`
   - To: `from src.thematic_lm.config import Settings`

3. **tests/unit/test_api.py**
   - Changed: `from thematic_lm.api.main import app`
   - To: `from src.thematic_lm.api.main import app`
   - Changed: `from thematic_lm.models.database import Analysis, AnalysisStatus`
   - To: `from src.thematic_lm.models.database import Analysis, AnalysisStatus`
   - Fixed all `patch()` paths to use `src.thematic_lm.api.routes.*`

4. **tests/integration/test_database.py**
   - Changed: `from thematic_lm.models.database import ...`
   - To: `from src.thematic_lm.models.database import ...`

5. **alembic/env.py**
   - Changed: `from thematic_lm.config import get_settings`
   - To: `from src.thematic_lm.config import get_settings`
   - Changed: `from thematic_lm.models.database import Base`
   - To: `from src.thematic_lm.models.database import Base`

6. **pyproject.toml**
   - Added hatchling configuration to specify package location

## Why This Was Needed

The project uses a `src` layout where the package is in `src/thematic_lm/`. This is a best practice for Python projects because:

1. **Prevents accidental imports** - Can't accidentally import from the source directory
2. **Tests the installed package** - Ensures tests run against the installed version
3. **Cleaner namespace** - Separates source from tests and other files

## Two Ways to Import

### Option 1: Install Package (Recommended)

```bash
# Install in editable mode
pip install -e .
# or
uv pip install -e .
```

Then import normally:
```python
from thematic_lm.config import Settings
from thematic_lm.models.database import Analysis
```

### Option 2: Use PYTHONPATH (For Development)

```bash
PYTHONPATH=. python script.py
```

Then import with `src.` prefix:
```python
from src.thematic_lm.config import Settings
from src.thematic_lm.models.database import Analysis
```

## Test Files

Test files use the `src.` prefix to work without requiring package installation. This allows:
- Running tests immediately after cloning
- CI/CD environments without installation step
- Faster development iteration

## Running Tests

```bash
# Tests work without installation
PYTHONPATH=. pytest tests/unit/

# Or install first
pip install -e .
pytest tests/unit/
```

## Verification

All imports now work correctly:

```bash
$ PYTHONPATH=. python3 -c "from src.thematic_lm.config import Settings; print('✅ Config imports work')"
✅ Config imports work

$ PYTHONPATH=. python3 -c "from src.thematic_lm.models.database import Analysis; print('✅ Database models import work')"
✅ Database models import work
```

## Summary

✅ All test files updated with correct import paths
✅ Alembic env.py updated
✅ pyproject.toml configured for src layout
✅ Tests can run without package installation
✅ Package can be installed for normal imports
