from pydantic import BaseModel, validator
from typing import Optional


class CategoryBase(BaseModel):
    name: str
    description: Optional[str]

    @validator("name")
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name must not be empty or whitespace")
        if len(v.strip()) < 2:
            raise ValueError("Name must be at least 2 characters long.")
        if len(v.strip()) > 100:
            raise ValueError("Name must be at most 100 characters long.")
        return v

    @validator("description")
    def description_max_length(cls, v: Optional[str]):
        if v and len(v) > 255:
            raise ValueError("Description must be at most 255 characters.")
        return v


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int

    class Config:
        from_attributes = True
