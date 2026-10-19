import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.integrations.groq_client import (
    GroqAssessmentClient,
    LLMConfigurationError,
    LLMProviderError,
    LLMResponseError,
)
from app.schemas.matching import (
    CandidateMatchingRequest,
    CandidateMatchingResponse,
)
from app.services.candidate_matching_service import (
    CandidateMatchingService,
)
from app.services.semantic_search_service import (
    SemanticSearchService,
)


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/matching",
    tags=["AI Matching"],
)


def get_candidate_matching_service(
    db: Session = Depends(get_db),
) -> CandidateMatchingService:
    try:
        assessment_client = GroqAssessmentClient()
    except LLMConfigurationError as exc:
        logger.error("AI matching configuration is missing")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI matching is not configured",
        ) from exc

    return CandidateMatchingService(
        search_service=SemanticSearchService(db),
        assessment_client=assessment_client,
    )


@router.post(
    "/candidates",
    response_model=CandidateMatchingResponse,
    status_code=status.HTTP_200_OK,
)
def match_candidates(
    request: CandidateMatchingRequest,
    service: CandidateMatchingService = Depends(
        get_candidate_matching_service
    ),
):
    try:
        results = service.match(
            job_description=request.job_description,
            limit=request.limit,
        )

    except LLMConfigurationError as exc:
        logger.error("AI matching configuration is missing")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI matching is not configured",
        ) from exc

    except LLMProviderError as exc:
        logger.warning("AI matching provider unavailable")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI matching is temporarily unavailable",
        ) from exc

    except LLMResponseError as exc:
        logger.warning("AI matching returned an invalid assessment")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI matching returned an invalid assessment",
        ) from exc

    return CandidateMatchingResponse(
        job_description=request.job_description,
        total=len(results),
        results=results,
    )