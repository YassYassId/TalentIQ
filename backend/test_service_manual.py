from app.db.session import SessionLocal
from app.schemas.candidate import CandidateCreate, CandidateUpdate
from app.services.candidate_service import CandidateService


def main():
    db = SessionLocal()

    try:
        service = CandidateService(db)

        # CREATE
        candidate = service.create(
            CandidateCreate(
                full_name="Jane Smith",
                email="jane@example.com",
                phone="+212622222222",
            )
        )

        print("Created:", candidate.id, candidate.full_name)

        # READ
        found = service.get_by_id(candidate.id)
        print("Found:", found.full_name)

        # UPDATE
        updated = service.update(
            candidate.id,
            CandidateUpdate(phone="+212633333333"),
        )
        print("Updated phone:", updated.phone)

        # LIST
        candidates = service.list_candidates()
        print("Candidates returned:", len(candidates))

        # DELETE
        service.delete(candidate.id)
        print("Candidate deleted successfully")

    finally:
        db.close()


if __name__ == "__main__":
    main()