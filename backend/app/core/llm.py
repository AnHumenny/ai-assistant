import re
from typing import TypeVar

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionMessageParam
from pydantic import BaseModel, ValidationError

from backend.app.core.config import settings
from backend.app.modules.assistant.schemas import ChatResponse

ResponseT = TypeVar("ResponseT", bound=BaseModel)
_CHAT_RESPONSE_FIELD = re.compile(
    r"^\s*(customer_reply|manager_hint)\s*:\s*", re.IGNORECASE | re.MULTILINE
)


def _parse_chat_response_text(content: str) -> dict[str, str] | None:
    """Extract the two labeled fields from a plain-text ChatResponse."""

    matches = list(_CHAT_RESPONSE_FIELD.finditer(content))
    if len(matches) != 2 or content[: matches[0].start()].strip():
        return None

    fields: dict[str, str] = {}
    for index, match in enumerate(matches):
        field_name = match.group(1).lower()
        if field_name in fields:
            return None

        value_end = matches[index + 1].start() if index + 1 < len(matches) else len(content)
        fields[field_name] = content[match.end() : value_end].strip()

    if set(fields) != {"customer_reply", "manager_hint"}:
        return None
    return fields


class LLMConfigurationError(RuntimeError):
    """Raised when an LLM request is attempted without required settings."""


class LLMEmptyResponseError(RuntimeError):
    """Raised when the LLM returns no usable message content."""


class LLMClient:
    """Send asynchronous chat completion requests with typed responses."""

    def __init__(self) -> None:
        self._client: AsyncOpenAI | None = None

    def _get_client(self) -> AsyncOpenAI:
        if self._client is None:
            if not settings.llm_api_key.strip():
                raise LLMConfigurationError(
                    "LLM_API_KEY must be set before making LLM requests."
                )

            client_options: dict[str, str] = {
                "api_key": settings.llm_api_key,
            }

            if settings.llm_base_url:
                client_options["base_url"] = settings.llm_base_url

            self._client = AsyncOpenAI(**client_options)

        return self._client

    async def complete_structured(
        self,
        messages: list[ChatCompletionMessageParam],
        response_format: type[ResponseT],
    ) -> ResponseT:
        """Request and parse a chat completion into the given Pydantic model."""

        completion = await self._get_client().chat.completions.create(
            model=settings.llm_model,
            messages=messages,
        )

        if not completion.choices:
            raise LLMEmptyResponseError("The LLM response did not contain choices.")

        content = completion.choices[0].message.content
        if not content or not content.strip():
            raise LLMEmptyResponseError("The LLM response did not contain message content.")

        try:
            return response_format.model_validate_json(content)
        except ValidationError as original_error:
            is_invalid_json = any(
                error["type"] == "json_invalid" for error in original_error.errors()
            )
            if response_format is ChatResponse and is_invalid_json:
                plain_text_fields = _parse_chat_response_text(content)
                if plain_text_fields is not None:
                    try:
                        return response_format.model_validate(plain_text_fields)
                    except ValidationError:
                        pass
            raise

    async def close(self) -> None:
        """Close the underlying HTTP client if it has been initialized."""

        if self._client is not None:
            await self._client.close()
            self._client = None


llm_client = LLMClient()
