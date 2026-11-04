from fastapi import APIRouter, HTTPException
from openai import RateLimitError

from backend.app.core.llm import LLMConfigurationError, LLMEmptyResponseError
from backend.app.modules.assistant.schemas import ChatRequest, ChatResponse
from backend.app.modules.assistant.service import process_message


router = APIRouter(tags=["assistant"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Report that the API is running."""
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        return await process_message(request.message)
    except LLMConfigurationError as error:
        raise HTTPException(
            status_code=503,
            detail="The LLM is not configured. Set LLM_API_KEY to enable chat.",
        ) from error
    except LLMEmptyResponseError as error:
        raise HTTPException(
            status_code=503,
            detail="The AI service returned an empty response. Please try again later.",
        ) from error
    except RateLimitError as error:
        raise HTTPException(
            status_code=503,
            detail="The AI service is temporarily unavailable. Please try again later.",
        ) from error
