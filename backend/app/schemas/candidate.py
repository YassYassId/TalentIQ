import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CandidateBase(BaseModel):
    full_name: str = Field(min_length=2, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)


class CandidateCreate(CandidateBase):
    pass


class CandidateUpdate(BaseModel):
    full_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=255,
    )
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)


class CandidateResponse(CandidateBase):
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)