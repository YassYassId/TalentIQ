import uuid

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.candidate_chunk import CandidateChunk


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