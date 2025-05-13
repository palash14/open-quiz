# File: src/app/schemas/user.py

from pydantic import BaseModel, EmailStr, Field, validator
from fastapi import HTTPException, status
from typing import Optional
from src.app.models.user import UserStatusEnum


class UserBase(BaseModel):
    email: EmailStr = Field(max_length=320)
    name: str = Field(
        min_length=3,
        max_length=200,
        description="Name must be between 3 and 200 characters.",
    )


class UserCreate(UserBase):
    password: str = Field(
        min_length=8,
        max_length=50,
        description="Password must be between 8 and 50 characters.",
    )

    @validator("email")
    def validate_email(cls, v):
        # Additional custom email validation (on top of Pydantic's EmailStr validation)
        regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(regex, v):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format!"
            )
        return v

    @validator("name")
    def validate_name(cls, v):
        if not v or v.strip() == "":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="name cannot be empty"
            )
        return v

    @validator("password")
    def validate_password_strength(cls, v):
        if not re.search(r"[A-Z]", v):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one uppercase letter",
            )
        if not re.search(r"[a-z]", v):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one lowercase letter",
            )
        if not re.search(r"[0-9]", v):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one number",
            )
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one special character",
            )
        if len(v) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long",
            )
        return v


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_no: Optional[str] = None
    dial_code: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone_no: Optional[str]
    dial_code: Optional[str]
    status: UserStatusEnum

    class Config:
        from_attributes = True


class UserNameResponse(BaseModel):
    name: str

    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="The current password of the user.",
    )
    new_password: str = Field(
        ..., min_length=8, max_length=100, description="The new password of the user."
    )
