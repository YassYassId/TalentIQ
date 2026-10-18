import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CandidateSearchRequest(BaseModel):
    query: str = Field(
        min_length=2,
        max_length=2000,
        description="Natural-language candidate search query",
    )

    limit: int = Field(default=10, ge=1, le=100)

    chunks_per_candidate: int = Field(default=3, ge=1, le=10)

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        value = value.strip()

        if len(value) < 2:
            raise ValueError(
                "Search query must contain at least 2 characters"
            )

        return value


class SearchMatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    content: str
    similarity: float


class CandidateSearchItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    candidate_id: uuid.UUID
    full_name: str
    email: str | None
    score: float
    matches: list[SearchMatchResponse]


class CandidateSearchResponse(BaseModel):
    query: str
    total: int
    results: list[CandidateSearchItem]