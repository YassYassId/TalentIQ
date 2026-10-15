from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.v1.candidates import router as candidates_router
from app.db.session import get_db

app = FastAPI(
    title="TalentIQ API",
    description="AI-powered recruitment platform",
    version="0.1.0",
)

app.include_router(
    candidates_router,
    prefix="/api/v1",
)


@app.get("/api/v1/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "talentiq-api",
        "version": "0.1.0",
    }

@app.get("/api/v1/health/db", tags=["Health"])
def database_health_check(
    db: Session = Depends(get_db),
):
    db.execute(text("SELECT 1"))

    return {
        "status": "healthy",
        "database": "postgresql",
    }