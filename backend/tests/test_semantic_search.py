import uuid

import pytest

from app.models.candidate import Candidate
from app.models.candidate_chunk import CandidateChunk
from app.repositories.candidate_chunk_repository import CandidateChunkRepository


def test_search_similar_chunks(db_session):
    candidate = Candidate(
    id=uuid.uuid4(),
    full_name="Test Candidate",
    email=f"candidate-{uuid.uuid4().hex}@example.com",
    )

    db_session.add(candidate)
    db_session.flush()

    vector_a = [1.0] + [0.0] * 383
    vector_b = [0.0, 1.0] + [0.0] * 382

    chunks = [
        CandidateChunk(
            candidate_id=candidate.id,
            chunk_index=0,
            content="Java Spring Boot Kafka",
            embedding=vector_a,
        ),
        CandidateChunk(
            candidate_id=candidate.id,
            chunk_index=1,
            content="Python Django Flask",
            embedding=vector_b,
        ),
    ]

    repository = CandidateChunkRepository(db_session)
    repository.save_all(chunks)

    results = repository.search_similar_chunks(
        query_embedding=vector_a,
        limit=2,
    )

    assert len(results) == 2

    first_chunk, first_score = results[0]
    second_chunk, second_score = results[1]

    assert first_chunk.content == "Java Spring Boot Kafka"
    assert first_score == pytest.approx(1.0, abs=1e-5)

    assert second_chunk.content == "Python Django Flask"
    assert second_score == pytest.approx(0.0, abs=1e-5)


@pytest.mark.parametrize(
    "embedding",
    [
        [],
        [0.1] * 100,
        [0.1] * 385,
    ],
)
def test_search_rejects_invalid_embedding_dimensions(
    db_session,
    embedding,
):
    repository = CandidateChunkRepository(db_session)

    with pytest.raises(ValueError, match="384 dimensions"):
        repository.search_similar_chunks(
            query_embedding=embedding,
        )


def test_search_rejects_invalid_limit(db_session):
    repository = CandidateChunkRepository(db_session)

    with pytest.raises(ValueError, match="Limit must be positive"):
        repository.search_similar_chunks(
            query_embedding=[1.0] + [0.0] * 383,
            limit=0,
        )

def test_search_ranks_distinct_candidates(db_session):
    first = Candidate(full_name="Ahmed")
    second = Candidate(full_name="Sara")
    third = Candidate(full_name="Youssef")

    db_session.add_all([first, second, third])
    db_session.flush()

    query_vector = [1.0] + [0.0] * 383
    medium_vector = [0.8, 0.6] + [0.0] * 382
    lower_vector = [0.6, 0.8] + [0.0] * 382

    db_session.add_all([
        CandidateChunk(
            candidate_id=first.id,
            chunk_index=0,
            content="Strong Java experience",
            embedding=query_vector,
        ),
        CandidateChunk(
            candidate_id=first.id,
            chunk_index=1,
            content="Spring Boot and Kafka",
            embedding=query_vector,
        ),
        CandidateChunk(
            candidate_id=second.id,
            chunk_index=0,
            content="Backend development",
            embedding=medium_vector,
        ),
        CandidateChunk(
            candidate_id=third.id,
            chunk_index=0,
            content="Software engineering",
            embedding=lower_vector,
        ),
    ])
    db_session.flush()

    repository = CandidateChunkRepository(db_session)

    results = repository.search_ranked_candidates(
        query_embedding=query_vector,
        limit=2,
        chunks_per_candidate=2,
    )

    candidate_ids = list(dict.fromkeys(
        candidate.id for candidate, _, _ in results
    ))

    assert candidate_ids == [first.id, second.id]
    assert len(results) == 3
    assert results[0][2] == pytest.approx(1.0)