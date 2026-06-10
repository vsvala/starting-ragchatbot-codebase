# Testing Infrastructure Changes

## Files Added

### `backend/tests/__init__.py`
Empty package marker.

### `backend/tests/conftest.py`
Shared pytest fixtures:
- `mock_rag_system` — `MagicMock` pre-wired with `query()`, `get_course_analytics()`, and `session_manager.create_session()` return values
- `test_app` — inline `FastAPI` app that mirrors the routes from `app.py` without static file mounting or ChromaDB initialisation; closes over `mock_rag_system` so per-test mutations are reflected
- `client` — `TestClient` wrapping `test_app`

### `backend/tests/test_api.py`
13 API endpoint tests across two classes:

**`TestQueryEndpoint`**
- `test_returns_answer_and_sources` — happy path response shape
- `test_uses_provided_session_id` — session_id passed through to RAG and returned
- `test_creates_session_when_none_provided` — session created automatically when omitted
- `test_returns_empty_sources_list` — empty sources list handled correctly
- `test_missing_required_query_field_returns_422` — validation error on missing `query`
- `test_empty_body_returns_422` — validation error on empty body
- `test_rag_error_returns_500` — RAG exception surfaces as 500 with detail message
- `test_response_has_all_required_fields` — all three fields present in response

**`TestCoursesEndpoint`**
- `test_returns_course_list` — correct count and titles
- `test_total_courses_matches_titles_length` — count is consistent with list length
- `test_response_has_all_required_fields` — both fields present
- `test_empty_course_list` — zero courses handled correctly
- `test_rag_error_returns_500` — RAG exception surfaces as 500 with detail message

## Files Modified

### `pyproject.toml`
Added pytest configuration and dev dependencies:

```toml
[dependency-groups]
dev = [
    "pytest>=8.0",
    "httpx>=0.27",
]

[tool.pytest.ini_options]
testpaths = ["backend/tests"]
pythonpath = ["backend"]
```

## Design Notes

`app.py` initialises `RAGSystem` at module level and mounts `StaticFiles` from `../frontend`, both of which fail in a test environment (no ChromaDB, no frontend build). The test app in `conftest.py` defines the same endpoint logic inline with a mocked `RAGSystem`, avoiding the import entirely. Tests that need to change mock behaviour (error cases) receive both `client` and `mock_rag_system` as fixtures — pytest gives them the same object instance within a test, so `side_effect` mutations work correctly.
