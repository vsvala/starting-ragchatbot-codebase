import sys
import os
import pytest
from unittest.mock import MagicMock
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel
from typing import List, Optional

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



_MOCK_ANSWER = "This is a mock answer about the course."
_MOCK_SOURCES = ["Python Basics - Lesson 1", "Python Basics - Lesson 2"]
_MOCK_SESSION_ID = "session_1"
_MOCK_COURSES = ["Python Basics", "Advanced Python", "Machine Learning"]


@pytest.fixture
def mock_rag_system():
    rag = MagicMock()
    rag.query.return_value = (_MOCK_ANSWER, _MOCK_SOURCES)
    rag.get_course_analytics.return_value = {
        "total_courses": len(_MOCK_COURSES),
        "course_titles": _MOCK_COURSES,
    }
    rag.session_manager.create_session.return_value = _MOCK_SESSION_ID
    return rag


@pytest.fixture
def test_app(mock_rag_system):
    """FastAPI app with real endpoint logic but a mocked RAGSystem.

    Mirrors the routes in app.py without static file mounting so tests
    run without a frontend build or ChromaDB instance.
    """
    app = FastAPI()

    class QueryRequest(BaseModel):
        query: str
        session_id: Optional[str] = None

    class QueryResponse(BaseModel):
        answer: str
        sources: List[str]
        session_id: str

    class CourseStats(BaseModel):
        total_courses: int
        course_titles: List[str]

    @app.post("/api/query", response_model=QueryResponse)
    async def query_documents(request: QueryRequest):
        try:
            session_id = request.session_id
            if not session_id:
                session_id = mock_rag_system.session_manager.create_session()
            answer, sources = mock_rag_system.query(request.query, session_id)
            return QueryResponse(answer=answer, sources=sources, session_id=session_id)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/courses", response_model=CourseStats)
    async def get_course_stats():
        try:
            analytics = mock_rag_system.get_course_analytics()
            return CourseStats(
                total_courses=analytics["total_courses"],
                course_titles=analytics["course_titles"],
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return app


@pytest.fixture
def client(test_app):
    return TestClient(test_app)
