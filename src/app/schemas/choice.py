from pydantic import BaseModel, validator
from typing import Optional


class ChoiceBase(BaseModel):
    option_text: str
    is_correct: bool = False

    @validator("option_text")
    def must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError("Option text must not be empty")
        if len(v.strip()) > 150:
            raise ValueError("Option text must be at most 150 characters long.")
        return v


class ChoiceSync(ChoiceBase):
    id: Optional[int]


class ChoiceResponse(ChoiceBase):
    id: int
    question_id: int

    class Config:
        from_attributes = True
