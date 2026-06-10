import sys
import os
import pytest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from vector_store import VectorStore, SearchResults
from models import Course, Lesson, CourseChunk


@pytest.fixture
def sample_course():
    return Course(
        title="Test RAG Course",
        course_link="https://example.com/course",
        instructor="Test Instructor",
        lessons=[
            Lesson(lesson_number=1, title="Introduction to RAG", lesson_link="https://example.com/lesson1"),
            Lesson(lesson_number=2, title="Vector Databases", lesson_link="https://example.com/lesson2"),
        ]
    )


@pytest.fixture
def sample_chunks():
    return [
        CourseChunk(
            content="RAG stands for Retrieval-Augmented Generation and enables AI to access external knowledge.",
            course_title="Test RAG Course",
            lesson_number=1,
            chunk_index=0
        ),
        CourseChunk(
            content="Vector databases store high-dimensional embeddings for semantic similarity search.",
            course_title="Test RAG Course",
            lesson_number=2,
            chunk_index=1
        ),
    ]


@pytest.fixture
def sample_search_results():
    return SearchResults(
        documents=["Content about RAG systems.", "Content about vector stores."],
        metadata=[
            {"course_title": "Test RAG Course", "lesson_number": 1, "chunk_index": 0},
            {"course_title": "Test RAG Course", "lesson_number": 2, "chunk_index": 1},
        ],
        distances=[0.1, 0.2]
    )


@pytest.fixture
def empty_search_results():
    return SearchResults(documents=[], metadata=[], distances=[])


@pytest.fixture
def error_search_results():
    return SearchResults.empty("Search error: Number of requested results 0 must be greater than 0.")


@pytest.fixture
def mock_vector_store():
    return MagicMock(spec=VectorStore)


@pytest.fixture(scope="session")
def seeded_vector_store(tmp_path_factory):
    """Real VectorStore with max_results=5, seeded with sample data."""
    tmp_path = tmp_path_factory.mktemp("chroma_seeded")
    store = VectorStore(str(tmp_path), "all-MiniLM-L6-v2", max_results=5)

    course = Course(
        title="Test RAG Course",
        course_link="https://example.com/course",
        instructor="Test Instructor",
        lessons=[
            Lesson(lesson_number=1, title="Introduction to RAG", lesson_link="https://example.com/lesson1"),
        ]
    )
    chunks = [
        CourseChunk(
            content="RAG stands for Retrieval-Augmented Generation and enables AI to access external knowledge.",
            course_title="Test RAG Course",
            lesson_number=1,
            chunk_index=0
        ),
        CourseChunk(
            content="Vector databases store high-dimensional embeddings for semantic similarity search.",
            course_title="Test RAG Course",
            lesson_number=1,
            chunk_index=1
        ),
    ]
    store.add_course_metadata(course)
    store.add_course_content(chunks)
    return store


@pytest.fixture(scope="session")
def broken_vector_store(tmp_path_factory):
    """Real VectorStore with max_results=0 — reproduces the MAX_RESULTS config bug."""
    tmp_path = tmp_path_factory.mktemp("chroma_broken")
    return VectorStore(str(tmp_path), "all-MiniLM-L6-v2", max_results=0)
