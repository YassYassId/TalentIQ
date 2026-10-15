import uuid

import pymupdf

from app.models.candidate import Candidate
from app.services.cv_processing_service import MAX_CV_SIZE


BASE_URL = "/api/v1/candidates"


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

    # Verify the extracted text was saved in PostgreSQL
    candidate = db_session.get(
        Candidate,
        uuid.UUID(candidate_id),
    )

    assert candidate is not None
    db_session.refresh(candidate)

    assert "Python" in candidate.cv_text
    assert "FastAPI" in candidate.cv_text
    assert "PostgreSQL" in candidate.cv_text


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