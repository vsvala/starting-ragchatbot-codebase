import pytest
from unittest.mock import MagicMock, patch

from vector_store import VectorStore, SearchResults
from search_tools import CourseSearchTool
from models import Course, Lesson, CourseChunk


# ── VectorStore / max_results bug ────────────────────────────────────────────

def test_max_results_zero_causes_search_error(broken_vector_store):
    """Reproduces the config bug: MAX_RESULTS=0 makes every search return an error."""
    results = broken_vector_store.search("What is RAG?")

    assert results.error is not None, (
        "Expected a search error when max_results=0, but got none. "
        "Check that config.MAX_RESULTS is set to a positive integer."
    )
    assert "error" in results.error.lower()


def test_search_returns_results_with_valid_max_results(seeded_vector_store):
    """Confirms that a correctly configured VectorStore (max_results=5) returns results."""
    results = seeded_vector_store.search("What is RAG?")

    assert results.error is None, f"Unexpected error with valid max_results: {results.error}"
    assert not results.is_empty(), "Expected results from seeded store, got none"
    assert len(results.documents) > 0


# ── CourseSearchTool with real ChromaDB ──────────────────────────────────────

def test_course_search_tool_with_real_store_returns_content(seeded_vector_store):
    """CourseSearchTool.execute() returns formatted content from real ChromaDB."""
    tool = CourseSearchTool(seeded_vector_store)
    result = tool.execute(query="RAG")

    assert isinstance(result, str)
    assert "Test RAG Course" in result
    assert len(result) > 0


def test_course_search_tool_broken_store_returns_error_string(broken_vector_store):
    """With max_results=0, the error propagates all the way up to the tool return value."""
    tool = CourseSearchTool(broken_vector_store)
    result = tool.execute(query="What is RAG?")

    assert "Search error" in result or "error" in result.lower()
    assert "Test RAG Course" not in result


# ── RAGSystem query flow ──────────────────────────────────────────────────────

def test_rag_system_query_invokes_ai_generator(tmp_path):
    """RAGSystem.query() calls generate_response and returns the AI's answer."""
    from rag_system import RAGSystem

    config = MagicMock()
    config.CHUNK_SIZE = 800
    config.CHUNK_OVERLAP = 100
    config.CHROMA_PATH = str(tmp_path / "chroma_rag")
    config.EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    config.MAX_RESULTS = 5
    config.MAX_HISTORY = 2
    config.ANTHROPIC_API_KEY = "fake-key"
    config.ANTHROPIC_MODEL = "claude-test"

    with patch("rag_system.AIGenerator") as MockAI, \
         patch("rag_system.VectorStore") as MockVS:
        mock_ai = MagicMock()
        mock_ai.generate_response.return_value = "RAG is a technique for augmenting AI with retrieval."
        MockAI.return_value = mock_ai
        MockVS.return_value = MagicMock()

        rag = RAGSystem(config)
        response, sources = rag.query("What is RAG?")

    assert mock_ai.generate_response.called
    assert response == "RAG is a technique for augmenting AI with retrieval."


def test_rag_system_sources_reset_after_query(tmp_path):
    """After query(), tool_manager.get_last_sources() returns [] (sources were retrieved and reset)."""
    from rag_system import RAGSystem

    config = MagicMock()
    config.CHUNK_SIZE = 800
    config.CHUNK_OVERLAP = 100
    config.CHROMA_PATH = str(tmp_path / "chroma_rag2")
    config.EMBEDDING_MODEL = "all-MiniLM-L6-v2"
    config.MAX_RESULTS = 5
    config.MAX_HISTORY = 2
    config.ANTHROPIC_API_KEY = "fake-key"
    config.ANTHROPIC_MODEL = "claude-test"

    with patch("rag_system.AIGenerator") as MockAI, \
         patch("rag_system.VectorStore") as MockVS:
        mock_ai = MagicMock()
        mock_ai.generate_response.return_value = "Answer"
        MockAI.return_value = mock_ai
        MockVS.return_value = MagicMock()

        rag = RAGSystem(config)
        rag.query("What is RAG?")

    assert rag.tool_manager.get_last_sources() == []
