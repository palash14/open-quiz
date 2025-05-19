# File: src/app/schemas/auth.py

from pydantic import BaseModel, EmailStr, Field, field_validator, FieldValidationInfo
from src.app.schemas.user import UserResponse
from src.app.schemas.validators import CommonValidators

class EmailVerifyValidator(BaseModel):
    email: EmailStr
    token: str = Field(
        ..., min_length=3, max_length=200,
        description="Token must be between 3 and 200 characters."
    )

    @field_validator("token")
    @classmethod
    def check_token(cls, v):
        return CommonValidators().validate_non_empty_token(v)

    @field_validator("email")
    @classmethod
    def check_email(cls, v):
        return CommonValidators().validate_email_format(v)


class ForgotPasswordValidator(BaseModel):
    email: EmailStr

    @field_validator("email")
    @classmethod
    def check_email(cls, v):
        return CommonValidators().validate_email_format(v)


class ResetPasswordValidator(BaseModel):
    email: EmailStr
    token: str = Field(
        ..., min_length=3, max_length=200,
        description="Token must be between 3 and 200 characters."
    )
    password: str = Field(
        ..., min_length=4, max_length=50,
        description="Password must be between 4 and 50 characters."
    )
    confirm_password: str = Field(...)

    @field_validator("token")
    @classmethod
    def check_token(cls, v):
        return CommonValidators().validate_non_empty_token(v)

    @field_validator("email")
    @classmethod
    def check_email(cls, v):
        return CommonValidators().validate_email_format(v)

    @field_validator("password")
    @classmethod
    def check_password(cls, v):
        return CommonValidators().validate_password_strength(v)
    
    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, confirm_password: str, info: FieldValidationInfo):
        password = info.data.get("password")
        if password is not None and confirm_password != password:
            raise ValueError("Passwords do not match.")
        return confirm_password


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class AuthRouterResponse(BaseModel):
    success: bool
    detail: str


class RegistrationResponse(AuthRouterResponse):
    user: UserResponse


class VerifyEmailRequest(AuthRouterResponse):
    email: str
    token: str


class Token(AuthRouterResponse):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
