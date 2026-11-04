from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    """A customer message submitted to the assistant."""

    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    """The customer-facing answer and manager-only suggestion."""

    model_config = ConfigDict(extra="forbid")

    customer_reply: str
    manager_hint: str
