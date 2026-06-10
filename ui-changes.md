# Quality Feature Changes

## Code Formatting with Black

### pyproject.toml
- Added `[dependency-groups] dev` with `black>=26.0.0`
- Added `[tool.black]` configuration: `line-length = 88`, `target-version = ["py312"]`
- Fixed `requires-python` to `>=3.12,<3.13` (matches root project)
- Added platform-pinned deps: `torch==2.2.2` and `numpy<2` for Intel Mac (`darwin/x86_64`)

### scripts/check_quality.sh (new file)
- `./scripts/check_quality.sh` — checks formatting, exits non-zero if any file is unformatted
- `./scripts/check_quality.sh --fix` — auto-formats all Python files
- Resolves `black` binary from: project `.venv` → repo root `.venv` → system `PATH`

### Python files formatted by black
All 10 files brought to consistent black style (double quotes, trailing commas, 88-char line wrap):
- `backend/app.py`
- `backend/ai_generator.py`
- `backend/config.py`
- `backend/document_processor.py`
- `backend/models.py`
- `backend/rag_system.py`
- `backend/search_tools.py`
- `backend/session_manager.py`
- `backend/vector_store.py`
- `main.py`
