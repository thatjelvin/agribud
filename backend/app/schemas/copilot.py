from pydantic import BaseModel


class CopilotQuestion(BaseModel):
    question: str
    farm_id: int | None = None


class CopilotAnswer(BaseModel):
    answer: str
    source: str
