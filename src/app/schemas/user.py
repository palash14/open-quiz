# File: src/app/schemas/user.py

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from src.app.models.user import UserStatusEnum


class UserBase(BaseModel):
    email: EmailStr = Field(max_length=320)
    name: str = Field(max_length=200)


class UserCreate(UserBase):
    password: str


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


class ForgotPasswordForm(BaseModel):
    email: str


class ResetPasswordForm(BaseModel):
    token: str
    new_password: str


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