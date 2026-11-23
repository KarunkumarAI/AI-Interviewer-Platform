from pydantic import BaseModel, Field
from typing import Literal
from uuid import UUID

Role = Literal["AI/ML Engineer", "Backend Engineer"]

class InterviewStart(BaseModel):
    role: Role
    resume_text: str = Field(min_length=80, max_length=30000)
    candidate_name: str | None = Field(default=None, max_length=120)

class AnswerIn(BaseModel):
    answer: str = Field(min_length=1, max_length=12000)

class InterviewOut(BaseModel):
    id: UUID
    role: str
    status: str
    current_question: dict | None = None
