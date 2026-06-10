import pytest
from fastapi.testclient import TestClient

MOCK_ANSWER = "This is a mock answer about the course."
MOCK_SOURCES = ["Python Basics - Lesson 1", "Python Basics - Lesson 2"]
MOCK_SESSION_ID = "session_1"
MOCK_COURSES = ["Python Basics", "Advanced Python", "Machine Learning"]


class TestQueryEndpoint:
    def test_returns_answer_and_sources(self, client):
        response = client.post("/api/query", json={"query": "What is Python?"})

        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == MOCK_ANSWER
        assert data["sources"] == MOCK_SOURCES

    def test_uses_provided_session_id(self, client, mock_rag_system):
        response = client.post(
            "/api/query",
            json={"query": "What is Python?", "session_id": "my-session"},
        )

        assert response.status_code == 200
        assert response.json()["session_id"] == "my-session"
        mock_rag_system.query.assert_called_once_with("What is Python?", "my-session")

    def test_creates_session_when_none_provided(self, client, mock_rag_system):
        response = client.post("/api/query", json={"query": "What is Python?"})

        assert response.status_code == 200
        assert response.json()["session_id"] == MOCK_SESSION_ID
        mock_rag_system.session_manager.create_session.assert_called_once()

    def test_returns_empty_sources_list(self, client, mock_rag_system):
        mock_rag_system.query.return_value = ("Answer with no sources", [])

        response = client.post("/api/query", json={"query": "General question"})

        assert response.status_code == 200
        assert response.json()["sources"] == []

    def test_missing_required_query_field_returns_422(self, client):
        response = client.post("/api/query", json={"session_id": "abc"})

        assert response.status_code == 422

    def test_empty_body_returns_422(self, client):
        response = client.post("/api/query", json={})

        assert response.status_code == 422

    def test_rag_error_returns_500(self, client, mock_rag_system):
        mock_rag_system.query.side_effect = Exception("DB connection failed")

        response = client.post("/api/query", json={"query": "What is Python?"})

        assert response.status_code == 500
        assert "DB connection failed" in response.json()["detail"]

    def test_response_has_all_required_fields(self, client):
        response = client.post("/api/query", json={"query": "What is Python?"})

        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "session_id" in data


class TestCoursesEndpoint:
    def test_returns_course_list(self, client):
        response = client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] == len(MOCK_COURSES)
        assert data["course_titles"] == MOCK_COURSES

    def test_total_courses_matches_titles_length(self, client):
        response = client.get("/api/courses")

        data = response.json()
        assert data["total_courses"] == len(data["course_titles"])

    def test_response_has_all_required_fields(self, client):
        response = client.get("/api/courses")

        data = response.json()
        assert "total_courses" in data
        assert "course_titles" in data

    def test_empty_course_list(self, client, mock_rag_system):
        mock_rag_system.get_course_analytics.return_value = {
            "total_courses": 0,
            "course_titles": [],
        }

        response = client.get("/api/courses")

        assert response.status_code == 200
        data = response.json()
        assert data["total_courses"] == 0
        assert data["course_titles"] == []

    def test_rag_error_returns_500(self, client, mock_rag_system):
        mock_rag_system.get_course_analytics.side_effect = Exception(
            "ChromaDB unavailable"
        )

        response = client.get("/api/courses")

        assert response.status_code == 500
        assert "ChromaDB unavailable" in response.json()["detail"]
