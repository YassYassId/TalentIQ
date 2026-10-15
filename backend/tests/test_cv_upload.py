import uuid

import pymupdf

from app.models.candidate import Candidate
from app.services.cv_processing_service import MAX_CV_SIZE
from app.models.candidate_chunk import CandidateChunk
from app.services.embedding_service import EmbeddingService
from sqlalchemy import select


BASE_URL = "/api/v1/candidates"

import pytest


@pytest.fixture(autouse=True)
def mock_embeddings(monkeypatch):
    def fake_embed_text(self, text: str) -> list[float]:
        if not text.strip():
            raise ValueError("Cannot embed empty text")

        return [0.1] * 384

    monkeypatch.setattr(
        EmbeddingService,
        "embed_text",
        fake_embed_text,
    )

    monkeypatch.setattr(
        EmbeddingService,
        "__init__",
        lambda self: None,
    )

def create_candidate(client):
    response = client.post(
        BASE_URL,
        json={
            "full_name": "Alice Johnson",
            "email": "alice@example.com",
        },
    )

    assert response.status_code == 201
    return response.json()["id"]


def generate_pdf(text: str | None = None) -> bytes:
    document = pymupdf.open()

    page = document.new_page()

    if text:
        page.insert_text(
            (72, 72),
            text,
            fontsize=12,
        )

    pdf_bytes = document.tobytes()
    document.close()

    return pdf_bytes


def upload_pdf(client, candidate_id, content, filename="cv.pdf"):
    return client.post(
        f"{BASE_URL}/{candidate_id}/cv",
        files={
            "file": (
                filename,
                content,
                "application/pdf",
            )
        },
    )


def test_upload_valid_pdf(client, db_session):
    candidate_id = create_candidate(client)

    pdf_content = generate_pdf(
        "Alice Johnson - Python, FastAPI, PostgreSQL"
    )

    response = upload_pdf(
        client,
        candidate_id,
        pdf_content,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["candidate_id"] == candidate_id
    assert data["filename"] == "cv.pdf"
    assert data["characters_extracted"] > 0

    # Verify extracted CV text
    candidate = db_session.get(
        Candidate,
        uuid.UUID(candidate_id),
    )

    assert candidate is not None
    db_session.refresh(candidate)

    assert "Python" in candidate.cv_text
    assert "FastAPI" in candidate.cv_text
    assert "PostgreSQL" in candidate.cv_text

    # Verify chunks and embeddings were persisted
    chunks = db_session.scalars(
        select(CandidateChunk)
        .where(
            CandidateChunk.candidate_id == uuid.UUID(candidate_id)
        )
        .order_by(CandidateChunk.chunk_index)
    ).all()

    assert len(chunks) == 1
    assert chunks[0].chunk_index == 0
    assert "FastAPI" in chunks[0].content
    assert len(chunks[0].embedding) == 384


def test_reject_non_pdf(client):
    candidate_id = create_candidate(client)

    response = client.post(
        f"{BASE_URL}/{candidate_id}/cv",
        files={
            "file": (
                "cv.txt",
                b"This is not a PDF",
                "text/plain",
            )
        },
    )

    assert response.status_code == 415


def test_reject_corrupted_pdf(client):
    candidate_id = create_candidate(client)

    response = upload_pdf(
        client,
        candidate_id,
        b"%PDF-1.7\nThis is not a valid PDF document",
    )

    assert response.status_code == 422


def test_reject_empty_pdf(client):
    candidate_id = create_candidate(client)

    response = upload_pdf(
        client,
        candidate_id,
        generate_pdf(),
    )

    assert response.status_code == 422


def test_reject_oversized_pdf(client):
    candidate_id = create_candidate(client)

    oversized_content = (
        b"%PDF-" + b"x" * MAX_CV_SIZE
    )

    response = upload_pdf(
        client,
        candidate_id,
        oversized_content,
    )

    assert response.status_code == 422
    assert "5 MB" in response.json()["detail"]


def test_candidate_not_found(client):
    unknown_id = uuid.uuid4()

    response = upload_pdf(
        client,
        unknown_id,
        generate_pdf("Test candidate CV"),
    )

    assert response.status_code == 404


def test_reject_zero_byte_file(client):
    candidate_id = create_candidate(client)

    response = upload_pdf(
        client,
        candidate_id,
        b"",
    )

    assert response.status_code == 422


def test_reupload_replaces_existing_chunks(client, db_session):
    candidate_id = create_candidate(client)

    first_pdf = generate_pdf(
        "Python FastAPI PostgreSQL developer"
    )

    first_response = upload_pdf(
        client,
        candidate_id,
        first_pdf,
    )

    assert first_response.status_code == 200

    second_pdf = generate_pdf(
        "Java Spring Boot Kafka developer"
    )

    second_response = upload_pdf(
        client,
        candidate_id,
        second_pdf,
    )

    assert second_response.status_code == 200

    db_session.expire_all()

    chunks = db_session.scalars(
        select(CandidateChunk)
        .where(
            CandidateChunk.candidate_id == uuid.UUID(candidate_id)
        )
    ).all()

    assert len(chunks) == 1
    assert "Java" in chunks[0].content
    assert "Kafka" in chunks[0].content
    assert "FastAPI" not in chunks[0].content

    candidate = db_session.get(
        Candidate,
        uuid.UUID(candidate_id),
    )

    assert "Spring Boot" in candidate.cv_text
    assert "PostgreSQL" not in candidate.cv_text



def test_embedding_failure_preserves_existing_cv(
    client,
    db_session,
    monkeypatch,
):
    candidate_id = create_candidate(client)

    original_pdf = generate_pdf(
        "Python FastAPI PostgreSQL developer"
    )

    response = upload_pdf(
        client,
        candidate_id,
        original_pdf,
    )

    assert response.status_code == 200

    def failing_embedding(self, text: str):
        raise RuntimeError("Embedding generation failed")

    monkeypatch.setattr(
        EmbeddingService,
        "embed_text",
        failing_embedding,
    )

    # The current API does not yet translate unexpected
    # embedding errors into a structured HTTP response.
    # TestClient therefore propagates the exception.
    with pytest.raises(
        RuntimeError,
        match="Embedding generation failed",
    ):
        upload_pdf(
            client,
            candidate_id,
            generate_pdf("Java Spring Boot developer"),
        )

    db_session.expire_all()

    candidate = db_session.get(
        Candidate,
        uuid.UUID(candidate_id),
    )

    assert "FastAPI" in candidate.cv_text
    assert "Spring Boot" not in candidate.cv_text

    chunks = db_session.scalars(
        select(CandidateChunk)
        .where(
            CandidateChunk.candidate_id == uuid.UUID(candidate_id)
        )
    ).all()

    assert len(chunks) == 1
    assert "FastAPI" in chunks[0].content