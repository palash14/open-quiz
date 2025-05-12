from pydantic import BaseModel, validator
from typing import Optional, List
from src.app.models.question import (
    QuestionTypeEnum,
    QuestionStatusEnum,
    QuestionDifficultyEnum,
)
from src.app.schemas.category import CategoryResponse
from src.app.schemas.choice import ChoiceResponse, ChoiceSync


class QuestionBase(BaseModel):
    question: str
    category_id: int
    question_type: QuestionTypeEnum
    difficulty: QuestionDifficultyEnum = QuestionDifficultyEnum.medium
    references: Optional[str] = None

    @validator("question")
    def question_must_not_be_empty(cls, value: str):
        if not value.strip():
            raise ValueError("Question must not be empty or whitespace.")
        if len(value.strip()) < 5:
            raise ValueError("Question must be at least 200 characters long.")
        if len(value.strip()) > 200:
            raise ValueError("Question must be at most 200 characters long.")
        return value

    @validator("references")
    def references_max_length(cls, value: Optional[str]):
        if value and len(value) > 10000:
            raise ValueError("Review comment must be at most 10000 characters.")
        return value


# For creating a question
class QuestionCreate(QuestionBase):
    choices: List[ChoiceSync] = []


# For updating a question
class QuestionUpdate(QuestionBase):
    pass


# Full question response with nested fields
class QuestionResponse(BaseModel):
    id: int
    user_id: int
    category: Optional[CategoryResponse]
    question: str
    question_type: QuestionTypeEnum
    status: QuestionStatusEnum
    difficulty: QuestionDifficultyEnum
    is_published: bool
    review_comment: Optional[str]
    explanation: Optional[str]

    choices: List[ChoiceResponse] = []

    class Config:
        from_attributes = True
