import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.candidate import Candidate


class CandidateRepository:

    def __init__(self, db: Session):
        self.db = db

    def create(self, candidate: Candidate) -> Candidate:
        self.db.add(candidate)
        self.db.flush()
        return candidate

    def find_by_id(self, candidate_id: uuid.UUID) -> Candidate | None:
        return self.db.get(Candidate, candidate_id)

    def find_all(self, offset: int = 0, limit: int = 20,) -> list[Candidate]:
        stmt = (
            select(Candidate)
            .order_by(Candidate.created_at.desc(), Candidate.id.desc())
            .offset(offset)
            .limit(limit)
        )

        return list(self.db.scalars(stmt).all())

    def delete(self, candidate: Candidate) -> None:
        self.db.delete(candidate)
        self.db.flush()