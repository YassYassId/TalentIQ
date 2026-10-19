from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.integrations.groq_client import (
    GroqAssessmentClient,
    LLMProviderError,
    LLMResponseError,
)


def make_completion(content, finish_reason="stop"):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                finish_reason=finish_reason,
                message=SimpleNamespace(content=content),
            )
        ]
    )


@pytest.fixture
def mock_groq():
    return Mock()


@pytest.fixture
def assessment_client(mock_groq):
    return GroqAssessmentClient(
        model="openai/gpt-oss-120b",
        client=mock_groq,
    )


def test_valid_structured_assessment(
    assessment_client,
    mock_groq,
):
    mock_groq.chat.completions.create.return_value = make_completion(
        """
        {
          "summary": "Spring Boot experience is documented.",
          "requirements": [
            {
              "requirement": "Spring Boot",
              "status": "supported",
              "evidence": ["Built APIs using Spring Boot"]
            }
          ],
          "limitations": []
        }
        """
    )

    result = assessment_client.assess(
        "System prompt",
        "User prompt",
    )

    assert result.requirements[0].status == "supported"

    kwargs = mock_groq.chat.completions.create.call_args.kwargs

    assert kwargs["response_format"]["type"] == "json_schema"
    assert kwargs["response_format"]["json_schema"]["strict"] is True


@pytest.mark.parametrize(
    "content",
    [
        "not json",
        '{"summary": "Test", "requirements": ["Spring Boot"]}',
        '{"summary": "", "requirements": [], "limitations": []}',
        '{"summary": "Test", "requirements": [{"requirement": "Java", "status": "supported", "evidence": []}], "limitations": []}',
    ],
)
def test_invalid_response_is_rejected(
    assessment_client,
    mock_groq,
    content,
):
    mock_groq.chat.completions.create.return_value = make_completion(
        content
    )

    with pytest.raises(LLMResponseError):
        assessment_client.assess("System", "User")


@pytest.mark.parametrize(
    "finish_reason",
    ["length", "content_filter"],
)
def test_incomplete_response_is_rejected(
    assessment_client,
    mock_groq,
    finish_reason,
):
    mock_groq.chat.completions.create.return_value = make_completion(
        "{}",
        finish_reason=finish_reason,
    )

    with pytest.raises(LLMResponseError):
        assessment_client.assess("System", "User")


def test_empty_choices_are_rejected(
    assessment_client,
    mock_groq,
):
    mock_groq.chat.completions.create.return_value = (
        SimpleNamespace(choices=[])
    )

    with pytest.raises(LLMResponseError):
        assessment_client.assess("System", "User")


def test_provider_failure_is_wrapped(
    assessment_client,
    mock_groq,
):
    mock_groq.chat.completions.create.side_effect = RuntimeError(
        "Simulated provider failure"
    )

    with pytest.raises(LLMProviderError):
        assessment_client.assess("System", "User")