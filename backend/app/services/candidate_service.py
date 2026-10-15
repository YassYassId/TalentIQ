import uuid

from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.repositories.candidate_repository import CandidateRepository
from app.schemas.candidate import CandidateCreate, CandidateUpdate


class CandidateNotFoundError(Exception):
    pass


class CandidateService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = CandidateRepository(db)

    def create(self, data: CandidateCreate) -> Candidate:
        candidate = Candidate(**data.model_dump())

        try:
            self.repository.create(candidate)
            self.db.commit()
            self.db.refresh(candidate)
            return candidate
        except Exception:
            self.db.rollback()
            raise

    def get_by_id(self, candidate_id: uuid.UUID) -> Candidate:
        candidate = self.repository.find_by_id(candidate_id)

        if candidate is None:
            raise CandidateNotFoundError(
                f"Candidate {candidate_id} not found"
            )

        return candidate

    def list_candidates(self, offset: int = 0, limit: int = 20,) -> list[Candidate]:
        return self.repository.find_all(offset, limit)

    def update(self, candidate_id: uuid.UUID, data: CandidateUpdate,) -> Candidate:
        candidate = self.get_by_id(candidate_id)

        updates = data.model_dump(exclude_unset=True)

        for field, value in updates.items():
            setattr(candidate, field, value)

        try:
            self.db.commit()
            self.db.refresh(candidate)
            return candidate
        except Exception:
            self.db.rollback()
            raise

    def delete(self, candidate_id: uuid.UUID) -> None:
        candidate = self.get_by_id(candidate_id)

        try:
            self.repository.delete(candidate)
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise