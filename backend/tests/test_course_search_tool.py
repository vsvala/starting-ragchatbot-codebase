import pytest
from unittest.mock import MagicMock
from search_tools import CourseSearchTool
from vector_store import SearchResults


def test_execute_basic_search(mock_vector_store, sample_search_results):
    mock_vector_store.search.return_value = sample_search_results
    mock_vector_store.get_lesson_link.return_value = None

    tool = CourseSearchTool(mock_vector_store)
    result = tool.execute(query="What is RAG?")

    assert "Test RAG Course" in result
    assert "Lesson 1" in result
    assert "Content about RAG systems." in result


def test_execute_passes_course_name_to_store(mock_vector_store, sample_search_results):
    mock_vector_store.search.return_value = sample_search_results
    mock_vector_store.get_lesson_link.return_value = None

    tool = CourseSearchTool(mock_vector_store)
    tool.execute(query="What is RAG?", course_name="RAG Course")

    mock_vector_store.search.assert_called_once_with(
        query="What is RAG?",
        course_name="RAG Course",
        lesson_number=None
    )


def test_execute_passes_lesson_number_to_store(mock_vector_store, sample_search_results):
    mock_vector_store.search.return_value = sample_search_results
    mock_vector_store.get_lesson_link.return_value = None

    tool = CourseSearchTool(mock_vector_store)
    tool.execute(query="What is RAG?", lesson_number=2)

    mock_vector_store.search.assert_called_once_with(
        query="What is RAG?",
        course_name=None,
        lesson_number=2
    )


def test_execute_empty_results_no_filter(mock_vector_store, empty_search_results):
    mock_vector_store.search.return_value = empty_search_results

    tool = CourseSearchTool(mock_vector_store)
    result = tool.execute(query="obscure topic")

    assert result == "No relevant content found."


def test_execute_empty_results_with_course_filter(mock_vector_store, empty_search_results):
    mock_vector_store.search.return_value = empty_search_results

    tool = CourseSearchTool(mock_vector_store)
    result = tool.execute(query="topic", course_name="MCP Course")

    assert "MCP Course" in result
    assert "No relevant content found" in result


def test_execute_empty_results_with_lesson_filter(mock_vector_store, empty_search_results):
    mock_vector_store.search.return_value = empty_search_results

    tool = CourseSearchTool(mock_vector_store)
    result = tool.execute(query="topic", lesson_number=3)

    assert "lesson 3" in result
    assert "No relevant content found" in result


def test_execute_propagates_store_error(mock_vector_store, error_search_results):
    mock_vector_store.search.return_value = error_search_results

    tool = CourseSearchTool(mock_vector_store)
    result = tool.execute(query="anything")

    assert "Search error" in result


def test_last_sources_populated_after_search(mock_vector_store, sample_search_results):
    mock_vector_store.search.return_value = sample_search_results
    mock_vector_store.get_lesson_link.return_value = "https://example.com/lesson1"

    tool = CourseSearchTool(mock_vector_store)
    tool.execute(query="What is RAG?")

    assert len(tool.last_sources) == 2
    assert tool.last_sources[0]["label"] == "Test RAG Course - Lesson 1"


def test_last_sources_empty_initially(mock_vector_store):
    tool = CourseSearchTool(mock_vector_store)
    assert tool.last_sources == []


def test_format_results_no_lesson_number(mock_vector_store):
    results_no_lesson = SearchResults(
        documents=["Course intro content."],
        metadata=[{"course_title": "Test RAG Course", "lesson_number": None}],
        distances=[0.1]
    )
    mock_vector_store.search.return_value = results_no_lesson

    tool = CourseSearchTool(mock_vector_store)
    result = tool.execute(query="overview")

    assert "Test RAG Course" in result
    assert "Lesson" not in result
