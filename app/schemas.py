from pydantic import BaseModel, Field


class MoodInput(BaseModel):
    score: int = Field(ge=1, le=5)


class JournalInput(BaseModel):
    answer: str = Field(min_length=2, max_length=2000)
    prompt: str = Field(default="What became clearer today?", max_length=500)


class CoachInput(BaseModel):
    question: str = Field(min_length=3, max_length=1000)


class TelegramUpdate(BaseModel):
    update_id: int
    message: dict[str, object] | None = None
