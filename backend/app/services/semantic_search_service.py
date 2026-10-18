import uuid
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.repositories.candidate_chunk_repository import (
    CandidateChunkRepository,
)
from app.services.embedding_service import EmbeddingService


@dataclass(frozen=True)
class SearchMatch:
    content: str
    similarity: float


@dataclass
class CandidateSearchResult:
    candidate_id: uuid.UUID
    full_name: str
    email: str | None
    score: float
    matches: list[SearchMatch] = field(default_factory=list)


class SemanticSearchService:
    def __init__(
        self,
        db: Session,
        embedding_service: EmbeddingService | None = None,
    ):
        self.repository = CandidateChunkRepository(db)
        self.embedding_service = (
            embedding_service
            if embedding_service is not None
            else EmbeddingService()
        )

    def search(
        self,
        query: str,
        limit: int = 10,
        chunks_per_candidate: int = 3,
    ) -> list[CandidateSearchResult]:
        query = query.strip()

        if not query:
            raise ValueError("Search query cannot be empty")

        if not 1 <= limit <= 100:
            raise ValueError("Limit must be between 1 and 100")

        if not 1 <= chunks_per_candidate <= 10:
            raise ValueError(
                "chunks_per_candidate must be between 1 and 10"
            )

        query_embedding = self.embedding_service.embed_text(query)

        rows = self.repository.search_ranked_candidates(
            query_embedding=query_embedding,
            limit=limit,
            chunks_per_candidate=chunks_per_candidate,
        )

        candidates: dict[uuid.UUID, CandidateSearchResult] = {}

        for candidate_record, chunk, similarity in rows:
            candidate_id = candidate_record.id

            if candidate_id not in candidates:
                candidates[candidate_id] = CandidateSearchResult(
                    candidate_id=candidate_id,
                    full_name=candidate_record.full_name,
                    email=candidate_record.email,
                    score=similarity,
                )

            candidates[candidate_id].matches.append(
                SearchMatch(
                    content=chunk.content,
                    similarity=similarity,
                )
            )

        return sorted(
            candidates.values(),
            key=lambda item: (-item.score, str(item.candidate_id)),
        )