# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Setup:**

```bash
uv sync                          # Install dependencies
uv add <package>                 # Add a new dependency
cp .env.example .env             # Then add ANTHROPIC_API_KEY to .env
```

use uv to run python files or add any dependencies

**Run the server:**

```bash
./run.sh
# or manually:
cd backend && uv run uvicorn app:app --reload --port 8000
```

The app is served at `http://localhost:8000` (frontend + API). Swagger docs at `/docs`.

**Python version:** Must be 3.12.x (see `pyproject.toml` — `>=3.12,<3.13`).

## Architecture

This is a full-stack RAG (Retrieval-Augmented Generation) chatbot that answers questions about course materials. No test suite exists.

**Request flow:**

1. Frontend (`frontend/`) sends `POST /api/query` with `{query, session_id}`
2. `backend/app.py` — FastAPI app; also serves the frontend as static files from `../frontend/`
3. `backend/rag_system.py` — `RAGSystem` orchestrates all components
4. `AIGenerator` calls Claude with the `search_course_content` tool available
5. Claude decides whether to invoke the tool; if so, `ToolManager` routes to `CourseSearchTool`
6. `CourseSearchTool` calls `VectorStore.search()` → ChromaDB query
7. Tool results are fed back to Claude for a final answer
8. `SessionManager` tracks conversation history (in-memory, per-process)

**Component responsibilities:**

| File                            | Responsibility                                                                                                 |
| ------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `backend/config.py`             | Single `Config` dataclass; all tuneable parameters (chunk size, model, max results, etc.)                      |
| `backend/models.py`             | Pydantic models: `Course`, `Lesson`, `CourseChunk`                                                             |
| `backend/document_processor.py` | Parses `.txt`/`.pdf`/`.docx` files into `Course` + `CourseChunk` objects; sentence-based chunking with overlap |
| `backend/vector_store.py`       | ChromaDB wrapper; two collections: `course_catalog` (course metadata) and `course_content` (chunked text)      |
| `backend/ai_generator.py`       | Wraps Anthropic SDK; handles the tool-use agentic loop                                                         |
| `backend/search_tools.py`       | `Tool` ABC, `CourseSearchTool`, `ToolManager`                                                                  |
| `backend/session_manager.py`    | In-memory conversation history; keyed by session ID                                                            |
| `backend/rag_system.py`         | Top-level orchestrator                                                                                         |

**Course document format** (files in `docs/`):

```
Course Title: <title>
Course Link: <url>
Course Instructor: <name>

Lesson 0: <title>
Lesson Link: <url>
<lesson content...>

Lesson 1: <title>
...
```

**ChromaDB persistence:** Stored at `backend/chroma_db/`. Documents are loaded from `../docs/` on startup; existing courses (by title) are skipped to avoid duplicates. To force a reload, call `add_course_folder(..., clear_existing=True)`.

**Vector database collections:**

- `course_catalog` — one document per course; used for semantic course name resolution
  - metadata: `title`, `instructor`, `course_link`, `lesson_count`, `lessons_json` (JSON string: list of `{lesson_number, lesson_title, lesson_link}`)
- `course_content` — one document per text chunk; used for semantic search
  - metadata: `course_title`, `lesson_number`, `chunk_index`

**Key config values** (`backend/config.py`):

- `ANTHROPIC_MODEL`: `claude-sonnet-4-6`
- `EMBEDDING_MODEL`: `all-MiniLM-L6-v2` (via sentence-transformers)
- `CHUNK_SIZE`: 800 chars, `CHUNK_OVERLAP`: 100 chars
- `MAX_RESULTS`: 5 (search results returned to Claude)
- `MAX_HISTORY`: 2 (conversation turns kept per session)

**Platform note:** `torch` and `numpy<2` are pinned only for Intel Macs (`darwin/x86_64`). Other platforms use sentence-transformers' default dependencies.
