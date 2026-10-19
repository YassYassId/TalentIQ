import uuid
from unittest.mock import Mock

import pytest

from app.integrations.groq_client import LLMResponseError
from app.schemas.matching import CandidateAssessment
from app.services.candidate_matching_service import (
    CandidateMatchingService,
)
from app.services.semantic_search_service import (
    CandidateSearchResult,
    SearchMatch,
)


@pytest.fixture
def candidate():
    return CandidateSearchResult(
        candidate_id=uuid.uuid4(),
        full_name="Test Candidate",
        email=None,
        score=0.91,
        matches=[
            SearchMatch(
                content="Built REST APIs using Spring Boot and Java.",
                similarity=0.91,
            )
        ],
    )


@pytest.fixture
def valid_assessment():
    return CandidateAssessment.model_validate({
        "summary": "The CV documents Java backend experience.",
        "requirements": [
            {
                "requirement": "Spring Boot",
                "status": "supported",
                "evidence": ["Spring Boot and Java"],
            },
            {
                "requirement": "Kafka",
                "status": "not_verified",
                "evidence": [],
            },
        ],
        "limitations": [
            "Only selected CV excerpts were available."
        ],
    })


def test_matches_candidate_with_grounded_evidence(
    candidate,
    valid_assessment,
):
    search = Mock()
    search.search.return_value = [candidate]

    llm = Mock()
    llm.assess.return_value = valid_assessment

    service = CandidateMatchingService(search, llm)

    results = service.match(
        "Looking for a Java Spring Boot and Kafka developer",
        limit=1,
    )

    assert len(results) == 1
    assert results[0].candidate_id == candidate.candidate_id
    assert results[0].assessment.requirements[0].status == "supported"

    search.search.assert_called_once_with(
        query="Looking for a Java Spring Boot and Kafka developer",
        limit=1,
        chunks_per_candidate=5,
    )
    llm.assess.assert_called_once()


def test_rejects_fabricated_evidence(candidate):
    search = Mock()
    search.search.return_value = [candidate]

    llm = Mock()
    llm.assess.return_value = CandidateAssessment.model_validate({
        "summary": "Candidate has Kubernetes experience.",
        "requirements": [
            {
                "requirement": "Kubernetes",
                "status": "supported",
                "evidence": [
                    "Managed Kubernetes clusters in production"
                ],
            }
        ],
        "limitations": [],
    })

    service = CandidateMatchingService(search, llm)

    with pytest.raises(
        LLMResponseError,
        match="unsupported evidence",
    ):
        service.match(
            "Looking for a Java developer with Kubernetes experience"
        )


def test_empty_search_skips_llm():
    search = Mock()
    search.search.return_value = []

    llm = Mock()

    service = CandidateMatchingService(search, llm)

    assert service.match(
        "Looking for an experienced Python backend developer"
    ) == []

    llm.assess.assert_not_called()


@pytest.mark.parametrize(
    "job_description, limit",
    [
        ("", 5),
        ("Short", 5),
        ("Java backend engineer with Spring Boot", 0),
        ("Java backend engineer with Spring Boot", 11),
    ],
)
def test_rejects_invalid_input(job_description, limit):
    search = Mock()
    llm = Mock()

    service = CandidateMatchingService(search, llm)

    with pytest.raises(ValueError):
        service.match(job_description, limit)

    search.search.assert_not_called()
    llm.assess.assert_not_called()