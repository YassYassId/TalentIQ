from app.db.session import SessionLocal
from app.models.candidate import Candidate
from app.repositories.candidate_repository import CandidateRepository


def main():
    db = SessionLocal()

    try:
        repo = CandidateRepository(db)

        candidate = Candidate(
            full_name="John Doe",
            email="john@example.com",
            phone="+212600000000",
        )

        # CREATE
        repo.create(candidate)
        db.commit()
        db.refresh(candidate)

        print("Created candidate:", candidate.id)

        # FIND BY ID
        found = repo.find_by_id(candidate.id)
        print("Found candidate:", found.full_name)

        # FIND ALL
        candidates = repo.find_all()
        print("Total candidates returned:", len(candidates))

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()