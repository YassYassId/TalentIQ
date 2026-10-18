from unittest.mock import Mock
import pytest

from app.api.v1.search import get_semantic_search_service
from app.main import app

from unittest.mock import patch

from app.models.candidate import Candidate
from app.models.candidate_chunk import CandidateChunk


def test_search_candidates_endpoint(client):
    service = Mock()
    service.search.return_value = []

    app.dependency_overrides[get_semantic_search_service] = (
        lambda: service
    )

    try:
        response = client.post(
            "/api/v1/search/candidates",
            json={
                "query": "Java Spring Boot developer",
                "limit": 10,
            },
        )

        assert response.status_code == 200
        assert response.json() == {
            "query": "Java Spring Boot developer",
            "total": 0,
            "results": [],
        }

        service.search.assert_called_once_with(
            query="Java Spring Boot developer",
            limit=10,
            chunks_per_candidate=3,
        )
    finally:
        app.dependency_overrides.pop(
            get_semantic_search_service,
            None,
        )


def test_search_rejects_empty_query(client):
    response = client.post(
        "/api/v1/search/candidates",
        json={"query": "   "},
    )

    assert response.status_code == 422


def test_search_rejects_invalid_limit(client):
    response = client.post(
        "/api/v1/search/candidates",
        json={
            "query": "Python developer",
            "limit": 0,
        },
    )

    assert response.status_code == 422


def test_search_rejects_missing_query(client):
    response = client.post(
        "/api/v1/search/candidates",
        json={},
    )

    assert response.status_code == 422


def test_search_candidates_end_to_end(client, db_session):
    candidate_a = Candidate(full_name="Ahmed")
    candidate_b = Candidate(full_name="Sara")

    db_session.add_all([candidate_a, candidate_b])
    db_session.flush()

    query_vector = [1.0] + [0.0] * 383

    db_session.add_all([
        CandidateChunk(
            candidate_id=candidate_a.id,
            chunk_index=0,
            content="Java Spring Boot Kafka",
            embedding=query_vector,
        ),
        CandidateChunk(
            candidate_id=candidate_b.id,
            chunk_index=0,
            content="Python FastAPI",
            embedding=[0.8, 0.6] + [0.0] * 382,
        ),
    ])
    db_session.flush()

    with patch(
        "app.services.semantic_search_service.EmbeddingService"
    ) as embedding_class:
        embedding_class.return_value.embed_text.return_value = (
            query_vector
        )

        response = client.post(
            "/api/v1/search/candidates",
            json={
                "query": "Java backend developer",
                "limit": 2,
                "chunks_per_candidate": 1,
            },
        )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 2
    assert len(data["results"]) == 2

    assert data["results"][0]["candidate_id"] == str(
        candidate_a.id
    )
    assert data["results"][0]["full_name"] == "Ahmed"
    assert data["results"][0]["score"] == pytest.approx(1.0)

    assert data["results"][1]["candidate_id"] == str(
        candidate_b.id
    )

    assert data["results"][0]["matches"][0]["content"] == (
        "Java Spring Boot Kafka"
    )