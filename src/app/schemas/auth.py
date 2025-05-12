# File: src/app/schemas/auth.py

from pydantic import BaseModel, EmailStr, Field, validator
from fastapi import HTTPException, status
import re


class EmailVerifyValidator(BaseModel):
    email: EmailStr
    email_verify_token: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Token must be between 3 and 200 characters.",
    )

    @validator("email_verify_token")
    def validate_email_verify_token(cls, v):
        if not v or v.strip() == "":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="token cannot be empty"
            )
        return v

    @validator("email")
    def validate_email(cls, v):
        # Additional custom email validation (on top of Pydantic's EmailStr validation)
        regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(regex, v):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format!"
            )
        return v


class ForgotPasswordValidator(BaseModel):
    email: EmailStr

    @validator("email")
    def validate_email(cls, v):
        # Additional custom email validation (on top of Pydantic's EmailStr validation)
        regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(regex, v):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format"
            )
        return v


class ResetPasswordValidator(BaseModel):
    email: EmailStr
    token: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Token must be between 3 and 200 characters.",
    )
    password: str = Field(
        ...,
        min_length=4,
        max_length=50,
        description="Password must be between 4 and 50 characters.",
    )

    @validator("token")
    def validate_token(cls, v):
        if not v or v.strip() == "":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="token cannot be empty"
            )
        return v

    @validator("email")
    def validate_email(cls, v):
        # Additional custom email validation (on top of Pydantic's EmailStr validation)
        regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(regex, v):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format"
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
