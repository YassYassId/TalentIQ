import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.candidate_chunk import CandidateChunk
from sqlalchemy import Float
from sqlalchemy import func
from app.models.candidate import Candidate


class CandidateChunkRepository:

    def __init__(self, db: Session):
        self.db = db

    def save_all(
        self,
        chunks: list[CandidateChunk],
    ) -> None:
        self.db.add_all(chunks)
        self.db.flush()

    def find_by_candidate_id(
        self,
        candidate_id: uuid.UUID,
    ) -> list[CandidateChunk]:
        statement = (
            select(CandidateChunk)
            .where(CandidateChunk.candidate_id == candidate_id)
            .order_by(CandidateChunk.chunk_index)
        )

        return list(self.db.scalars(statement).all())

    def delete_by_candidate_id(
        self,
        candidate_id: uuid.UUID,
    ) -> None:
        statement = (
            delete(CandidateChunk)
            .where(CandidateChunk.candidate_id == candidate_id)
        )

        self.db.execute(statement)

    def search_similar_chunks(self, query_embedding: list[float], limit: int = 20,) -> list[tuple[CandidateChunk, float]]:
        if len(query_embedding) != 384:
            raise ValueError("Query embedding must have 384 dimensions")

        if limit < 1:
            raise ValueError("Limit must be positive")

        distance = CandidateChunk.embedding.cosine_distance(query_embedding)

        statement = (
            select(CandidateChunk,(1.0 - distance).cast(Float).label("similarity"),)
            .order_by(distance.asc(), CandidateChunk.id.asc())
            .limit(limit)
        )

        rows = self.db.execute(statement).all()

        return [
            (chunk, float(similarity))
            for chunk, similarity in rows
        ]


    def search_ranked_candidates(
        self,
        query_embedding: list[float],
        limit: int = 10,
        chunks_per_candidate: int = 3,
        ) -> list[tuple[Candidate, CandidateChunk, float]]:
        if len(query_embedding) != 384:
            raise ValueError("Query embedding must have 384 dimensions")

        if limit < 1 or chunks_per_candidate < 1:
            raise ValueError("Limits must be positive")

        distance = CandidateChunk.embedding.cosine_distance(
            query_embedding
        )

        ranked_chunks = (
            select(
                CandidateChunk.id.label("chunk_id"),
                CandidateChunk.candidate_id.label("candidate_id"),
                distance.label("distance"),
                func.row_number().over(
                    partition_by=CandidateChunk.candidate_id,
                    order_by=(distance.asc(), CandidateChunk.id.asc()),
                ).label("chunk_rank"),
            )
            .cte("ranked_chunks")
        )

        best_candidates = (
            select(
                ranked_chunks.c.candidate_id,
                func.min(ranked_chunks.c.distance).label("best_distance"),
            )
            .where(ranked_chunks.c.chunk_rank == 1)
            .group_by(ranked_chunks.c.candidate_id)
            .order_by(
                func.min(ranked_chunks.c.distance).asc(),
                ranked_chunks.c.candidate_id.asc(),
            )
            .limit(limit)
            .cte("best_candidates")
        )

        statement = (
            select(
                Candidate,
                CandidateChunk,
                (1.0 - ranked_chunks.c.distance).label("similarity"),
            )
            .join(
                ranked_chunks,
                CandidateChunk.id == ranked_chunks.c.chunk_id,
            )
            .join(
                best_candidates,
                ranked_chunks.c.candidate_id
                == best_candidates.c.candidate_id,
            )
            .join(
                Candidate,
                Candidate.id == CandidateChunk.candidate_id,
            )
            .where(ranked_chunks.c.chunk_rank <= chunks_per_candidate)
            .order_by(
                best_candidates.c.best_distance.asc(),
                best_candidates.c.candidate_id.asc(),
                ranked_chunks.c.chunk_rank.asc(),
            )
        )

        return [
            (candidate, chunk, float(similarity))
            for candidate, chunk, similarity in self.db.execute(statement)
        ]