from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: str = Field(None, max_length=255)

    @validator("name")
    def name_must_not_be_blank(cls, v):
        if not v.strip():
            raise ValueError("Category name must not be blank")
        return v


class CategoryUpdate(CategoryBase):
    deleted_at: Optional[datetime] = None


class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True
