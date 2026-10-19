import logging
from app.core.config import settings

from groq import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    Groq,
    RateLimitError,
)
from pydantic import ValidationError

from app.schemas.matching import CandidateAssessment


logger = logging.getLogger(__name__)


class LLMConfigurationError(Exception):
    pass


class LLMProviderError(Exception):
    pass


class LLMResponseError(Exception):
    pass


class GroqAssessmentClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        client: Groq | None = None,
    ):
        self.model = model or settings.GROQ_MODEL

        if client is not None:
            self.client = client
            return

        resolved_key = api_key or (
            settings.GROQ_API_KEY.get_secret_value()
            if settings.GROQ_API_KEY is not None
            else None
        )

        if not resolved_key:
            raise LLMConfigurationError(
                "GROQ_API_KEY is not configured"
            )

        self.client = Groq(
            api_key=resolved_key,
            timeout=20.0,
            max_retries=1,
        )

    def assess(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> CandidateAssessment:
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                temperature=0,
                max_completion_tokens=1800,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "candidate_assessment",
                        "strict": True,
                        "schema": CandidateAssessment.model_json_schema(),
                    },
                },
            )

        except (APIConnectionError, APITimeoutError) as exc:
            logger.warning(
                "Groq connection or timeout failure: %s",
                type(exc).__name__,
            )
            raise LLMProviderError(
                "Assessment provider is unreachable"
            ) from exc

        except RateLimitError as exc:
            logger.warning("Groq rate limit exceeded")
            raise LLMProviderError(
                "Assessment provider rate limit exceeded"
            ) from exc

        except APIStatusError as exc:
            logger.warning(
                "Groq returned HTTP %s",
                exc.status_code,
            )
            raise LLMProviderError(
                "Assessment provider request failed"
            ) from exc

        except Exception as exc:
            logger.exception("Unexpected Groq request failure")
            raise LLMProviderError(
                "Assessment provider request failed"
            ) from exc

        if not completion.choices:
            raise LLMResponseError(
                "Assessment provider returned no choices"
            )

        choice = completion.choices[0]

        if choice.finish_reason != "stop":
            raise LLMResponseError(
                "Assessment provider returned an incomplete response"
            )

        content = choice.message.content

        if not content:
            raise LLMResponseError(
                "Assessment provider returned empty content"
            )

        try:
            return CandidateAssessment.model_validate_json(content)

        except ValidationError as exc:
            raise LLMResponseError(
                "Assessment provider returned invalid structured data"
            ) from exc