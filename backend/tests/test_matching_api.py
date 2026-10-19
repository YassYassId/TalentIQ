import uuid
from unittest.mock import Mock

import pytest

from app.api.v1.matching import get_candidate_matching_service
from app.integrations.groq_client import (
    LLMProviderError,
    LLMResponseError,
)
from app.main import app
from app.schemas.matching import CandidateAssessment
from app.services.candidate_matching_service import MatchingResult


JOB_DESCRIPTION = (
    "Looking for a backend developer with Java, "
    "Spring Boot, REST APIs and Kafka experience."
)


@pytest.fixture
def mocked_matching_service():
    service = Mock()

    app.dependency_overrides[get_candidate_matching_service] = (
        lambda: service
    )

    yield service

    app.dependency_overrides.pop(
        get_candidate_matching_service,
        None,
    )


def test_matching_returns_structured_assessment(
    client,
    mocked_matching_service,
):
    candidate_id = uuid.uuid4()

    assessment = CandidateAssessment.model_validate({
        "summary": "The CV documents Spring Boot experience.",
        "requirements": [
            {
                "requirement": "Spring Boot",
                "status": "supported",
                "evidence": ["Built APIs with Spring Boot"],
            },
            {
                "requirement": "Kafka",
                "status": "not_verified",
                "evidence": [],
            },
        ],
        "limitations": [
            "Only selected CV excerpts were evaluated."
        ],
    })

    mocked_matching_service.match.return_value = [
        MatchingResult(
            candidate_id=candidate_id,
            full_name="Test Candidate",
            assessment=assessment,
        )
    ]

    response = client.post(
        "/api/v1/matching/candidates",
        json={
            "job_description": JOB_DESCRIPTION,
            "limit": 1,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert data["results"][0]["candidate_id"] == str(candidate_id)
    assert data["results"][0]["full_name"] == "Test Candidate"
    assert (
        data["results"][0]["assessment"]["requirements"][0]["status"]
        == "supported"
    )

    mocked_matching_service.match.assert_called_once_with(
        job_description=JOB_DESCRIPTION,
        limit=1,
    )


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"job_description": "Too short"},
        {"job_description": JOB_DESCRIPTION, "limit": 0},
        {"job_description": JOB_DESCRIPTION, "limit": 11},
        {"job_description": " " * 30},
    ],
)
def test_matching_rejects_invalid_requests(client, payload):
    response = client.post(
        "/api/v1/matching/candidates",
        json=payload,
    )

    assert response.status_code == 422


@pytest.mark.parametrize(
    "exception, expected_status",
    [
        (LLMProviderError("Provider unavailable"), 503),
        (LLMResponseError("Invalid assessment"), 502),
    ],
)
def test_matching_handles_provider_errors(
    client,
    mocked_matching_service,
    exception,
    expected_status,
):
    mocked_matching_service.match.side_effect = exception

    response = client.post(
        "/api/v1/matching/candidates",
        json={"job_description": JOB_DESCRIPTION},
    )

    assert response.status_code == expected_status
    assert "detail" in response.json()