# Quality Feature Changes

## Black Code Formatter

Added `black` as a dev dependency for automatic, consistent Python code formatting.

### pyproject.toml

- Added `[dependency-groups]` section with `black>=26.0.0`
- Added `[tool.black]` config: `line-length = 88`, `target-version = ["py312"]`

### Files Reformatted

All 9 backend Python files were reformatted by black:

- `backend/config.py`
- `backend/models.py`
- `backend/session_manager.py`
- `backend/ai_generator.py`
- `backend/app.py`
- `backend/rag_system.py`
- `backend/search_tools.py`
- `backend/document_processor.py`
- `backend/vector_store.py`

Formatting changes were cosmetic only (no logic changes):
- Trailing whitespace removed
- Blank lines normalized around class and function definitions
- Inline comment spacing standardized to single space after `#`

### scripts/check_quality.sh

New script for running formatting checks:

```bash
./scripts/check_quality.sh        # Check formatting (CI-friendly, exits non-zero on failure)
./scripts/check_quality.sh --fix  # Auto-format all files in place
```

Black is resolved in order: project `.venv` → repo root `.venv` → system `PATH`.
