import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.candidate import (
    CandidateCreate,
    CandidateResponse,
    CandidateUpdate,
)
from app.services.candidate_service import (
    CandidateNotFoundError,
    CandidateService,
)

router = APIRouter(
    prefix="/candidates",
    tags=["Candidates"],
)


def get_candidate_service(
    db: Session = Depends(get_db),
) -> CandidateService:
    return CandidateService(db)


@router.post(
    "",
    response_model=CandidateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_candidate(
    data: CandidateCreate,
    service: CandidateService = Depends(get_candidate_service),
):
    return service.create(data)


@router.get(
    "",
    response_model=list[CandidateResponse],
)
def list_candidates(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    service: CandidateService = Depends(get_candidate_service),
):
    return service.list_candidates(offset=offset, limit=limit)


@router.get(
    "/{candidate_id}",
    response_model=CandidateResponse,
)
def get_candidate(
    candidate_id: uuid.UUID,
    service: CandidateService = Depends(get_candidate_service),
):
    try:
        return service.get_by_id(candidate_id)
    except CandidateNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{candidate_id}",
    response_model=CandidateResponse,
)
def update_candidate(
    candidate_id: uuid.UUID,
    data: CandidateUpdate,
    service: CandidateService = Depends(get_candidate_service),
):
    try:
        return service.update(candidate_id, data)
    except CandidateNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{candidate_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_candidate(
    candidate_id: uuid.UUID,
    service: CandidateService = Depends(get_candidate_service),
):
    try:
        service.delete(candidate_id)
    except CandidateNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc