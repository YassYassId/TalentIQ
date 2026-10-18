from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.search import (
    CandidateSearchRequest,
    CandidateSearchResponse,
)
from app.services.semantic_search_service import (
    SemanticSearchService,
)


router = APIRouter(
    prefix="/search",
    tags=["Search"],
)


def get_semantic_search_service(
    db: Session = Depends(get_db),
) -> SemanticSearchService:
    return SemanticSearchService(db)


@router.post(
    "/candidates",
    response_model=CandidateSearchResponse,
)
def search_candidates(
    request: CandidateSearchRequest,
    service: SemanticSearchService = Depends(
        get_semantic_search_service
    ),
):
    results = service.search(
        query=request.query,
        limit=request.limit,
        chunks_per_candidate=request.chunks_per_candidate,
    )

    return CandidateSearchResponse(
        query=request.query,
        total=len(results),
        results=results,
    )