from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)
import uuid



class RequirementAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    requirement: str = Field(min_length=1)
    status: Literal["supported", "not_verified"]
    evidence: list[str]

    @model_validator(mode="after")
    def validate_evidence(self):
        if self.status == "supported" and not self.evidence:
            raise ValueError(
                "Supported requirements must include evidence"
            )

        if self.status == "not_verified" and self.evidence:
            raise ValueError(
                "Unverified requirements cannot include evidence"
            )

        return self


class CandidateAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1, max_length=1500)
    requirements: list[RequirementAssessment]
    limitations: list[str]

class CandidateMatchingRequest(BaseModel):
      job_description: str = Field(
          min_length=20,
          max_length=10000,
          description="Job description used to assess candidates",
      )
      limit: int = Field(default=5, ge=1, le=10)
  
      @field_validator("job_description")
      @classmethod
      def validate_job_description(cls, value: str) -> str:
          value = value.strip()
          if len(value) < 20:
              raise ValueError(
                  "Job description must contain at least 20 characters"
              )
          return value
  
  
class CandidateMatchingItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    candidate_id: uuid.UUID
    full_name: str
    assessment: CandidateAssessment


class CandidateMatchingResponse(BaseModel):
    job_description: str
    total: int
    results: list[CandidateMatchingItem]