from typing import Annotated
from fastapi import APIRouter, Form, Depends, status, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, ValidationError
from datetime import datetime, timezone, timedelta
from src.app.core.database import get_db, get_field_value
from src.app.utils.exceptions import handle_router_exception
from src.app.schemas.user import UserCreate, UserResponse
from src.app.utils.hashing import verify_password, hash_password
from src.app.utils.jwt import (
    create_jwt_token,
    decode_jwt_token,
    get_client_ip,
    get_user_agent,
    create_user_token,
)
from src.app.core.config import settings
from src.app.utils.auth_validator import ForgotPasswordValidator
from src.app.services.user_service import find_one
from src.app.core.logger import create_logger

auth_logger = create_logger("auth_logger", "route_auth.log")

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={404: {"description": "Not found"}},
)


class RegistrationForm(BaseModel):
    user: UserCreate


class RegistrationResponse(BaseModel):
    success: bool
    detail: str
    user: UserResponse


class VerifyEmailForm(BaseModel):
    email: str
    token: str


class VerifyEmailResponse(BaseModel):
    success: bool
    detail: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


@router.post(
    "/register",
    summary="Register a new user",
    description="This endpoint registers a new user in the system.",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    request: RegistrationForm,
    db: Annotated[Session, Depends(get_db)],
) -> RegistrationResponse:
    """
    Handles the registration of a user and sends an email verification link.

    :param request: The registration form containing user data.
    :param db: The SQLAlchemy session dependency.
    :return: A structured response indicating the success of the registration.
    :raises HTTPException: If a database error occurs during registration.
    """
    try:
        # Validate incoming request
        validated_data = RegistrationFormValidator(**request.model_dump())

        # Check if the email already exists
        existing_user_by_email = get_field_value(
            db, "users", "email", validated_data.user.email
        )

        if existing_user_by_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )
        # Create user records
        new_user = user.create(db, None, validated_data.user)

        # Generate email verification token
        email_otp = generate_uuid()

        # Queue the email verification task
        send_verification_email_task.apply_async(
            args=[new_user.email, email_otp], queue="email_queue"
        )

        # Commit the transaction after all operations are successful
        db.commit()

        # Prepare and return success response
        return RegistrationResponse(
            success=True,
            detail="Registration completed successfully. Please check your email for verification.",
            user=UserResponse.model_validate(new_user),
        )

    except ValidationError as e:
        # If a Pydantic validation error occurs, return a 400 error with details
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.errors(),
        )

    except HTTPException as http_exc:
        # Re-raise known HTTP exceptions
        raise http_exc

    except Exception as e:
        db.rollback()
        # Log the exception (in real-world application, use proper logging)
        print(f"Unhandled exception: {e}")
        auth_logger.error(f"An error occurred while creating a user: {e}")
        handle_router_exception(e)


@router.post(
    "/verify-email",
    summary="Verify user's email address",
    description="This endpoint verifies a user's email address.",
    response_class=JSONResponse,
)
def verify_email(
    db: Annotated[Session, Depends(get_db)],
    email: str = Form(...),
    token: str = Form(...),
):
    """
    Verifies the user's email address using the provided token and user ID. It updates the
    email_verified_at field if the verification is successful.

    :param request: The verification form containing Email and token.
    :param db: The SQLAlchemy session dependency.
    :return: A structured response indicating the success of the email verification.
    :raises HTTPException: If the user is not found, the token is invalid, or the email is already verified.
    """
    try:

        result = user.find_one(db, email=email, email_verify_token=token)

        if not result:
            return JSONResponse(
                content="Verification Failed,Invalid email or token. Please try again",
                status_code=400,
            )

        if result.email_verified_at is not None:
            return JSONResponse(
                content="Email address already verified.", status_code=400
            )

        # Check if the token has expired
        if result.email_verify_expired_at:
            email_expiry = result.email_verify_expired_at.replace(
                tzinfo=timezone.utc
            ).strftime("%Y%m%d%H%I")
            today = datetime.now(timezone.utc).strftime("%Y%m%d%H%I")
            if email_expiry < today:
                return JSONResponse(
                    content="Verification Failed,Token has expired. Please request a new verification email.",
                    status_code=400,
                )
        else:
            return JSONResponse(
                content="Verification Failed,Token has expired. Please request a new verification email.",
                status_code=400,
            )

        # Update the user's email_verified_at field
        result.email_verified_at = datetime.now().replace(tzinfo=timezone.utc)
        result.email_verify_token = None  # Invalidate the token after verification
        result.email_verify_expired_at = None
        db.commit()  # Commit the changes to the database
        db.refresh(result)  # Refresh the instance with updated data
        return JSONResponse(
            content="Email address verified successfully.", status_code=200
        )

    except HTTPException as http_exc:
        # Re-raise known HTTP exceptions
        raise http_exc

    except Exception as e:
        db.rollback()  # Rollback any changes if an error occurs
        # Log the exception (in a real-world application, use proper logging)
        print(f"Unhandled exception: {e}")
        auth_logger.error(f"An error occurred while verify email: {e}")
        handle_router_exception(e)


@router.post(
    "/login",
    summary="Login and get JWT token",
    description="This endpoint logs in a user and returns a JWT token.",
    response_model=Token,
    status_code=status.HTTP_200_OK,
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    request: Request,
    db: Annotated[Session, Depends(get_db)],
) -> Token:
    """
    Handles user login, verifies credentials, and returns a JWT token.

    :param form_data:
    :param request: The login form containing username(email address) and password.
    :param db: The SQLAlchemy session dependency.
    :return: A structured response with the JWT token.
    :raises HTTPException: If user credentials are invalid or not found.
    """
    try:
        user_data = user.find_one(db, email=form_data.username)

        if not user_data or not verify_password(form_data.password, user_data.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if user_data.email_verified_at is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address not verified.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create JWT token
        access_token, refresh_token = create_jwt_token(subject=form_data.username)
        create_user_token(
            db=db,
            user_id=user_data.id,
            access_token=access_token,
            refresh_token=refresh_token,
            ip=get_client_ip(request),
            user_agent=get_user_agent(request),
            expired_at=datetime.now()
            + timedelta(minutes=int(settings.ACCESS_TOKEN_EXPIRE_MINUTES)),
        )
        return Token(access_token=access_token, refresh_token=refresh_token)

    except Exception as e:
        print(f"{e}")
        auth_logger.error(f"An error occurred while login: {e}")
        handle_router_exception(e)


@router.post(
    "/refresh-token",
    summary="Login and get JWT token",
    description="This endpoint logs in a user and returns a JWT token.",
    response_model=Token,
    status_code=status.HTTP_200_OK,
)
async def refresh_access_token(refresh_token: str):
    try:
        payload = decode_jwt_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=400, detail="Invalid token type")

        new_access_token, refresh_token = create_jwt_token(subject=payload["sub"])
        return Token(access_token=new_access_token, refresh_token=refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post(
    "/forgot-password",
    summary="Send a password reset email",
    description="This endpoint sends a password reset email to the user.",
    response_model=VerifyEmailResponse,
    status_code=status.HTTP_200_OK,
)
def forgot_password(
    request: ForgotPasswordValidator,
    db: Annotated[Session, Depends(get_db)],
) -> VerifyEmailResponse:
    """
    Handles the forgot password request. It generates a reset token and sends an email.

    :param request: The form containing the user's email.
    :param db: The SQLAlchemy session dependency.
    :return: A structured response indicating the success of the operation.
    :raises HTTPException: If the user is not found.
    """
    try:
        user_data = user.find_one(db, email=request.email)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        # Generate password reset token
        reset_token = generate_uuid()

        email_token_expired_at = datetime.today() + timedelta(1)
        # Update the user's email_verified_at field
        user_data.email_verify_token = reset_token
        user_data.email_verify_expired_at = email_token_expired_at
        db.commit()  # Commit the changes to the database
        db.refresh(user_data)  # Refresh the instance with updated data

        # Queue the password reset email task
        send_forgot_email_task.apply_async(
            args=[request.email, reset_link], queue="email_queue"
        )

        return VerifyEmailResponse(
            success=True, detail="Password reset email sent successfully."
        )

    except ValidationError as e:
        # If a Pydantic validation error occurs, return a 400 error with details
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"detail": e.errors()}
        )

    except Exception as e:
        print(f"Unhandled exception: {e}")
        auth_logger.error(f"An error occurred while forgot password: {e}")
        handle_router_exception(e)


@router.post(
    "/reset-password",
    summary="Reset user password",
    description="This endpoint resets the user's password using the provided token.",
    response_class=JSONResponse,
)
def reset_password(
    db: Annotated[Session, Depends(get_db)],
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    token: str = Form(...),
):
    """
    Handle password reset requests by validating the token and updating the password.

    :param email: The user's email address.
    :param password: The new password provided by the user.
    :param confirm_password: The confirmation of the new password.
    :param token: The verification token.
    :param db: The SQLAlchemy session.
    :return: HTML response indicating success or failure.
    """
    try:
        # Validate the passwords match
        if password != confirm_password:
            return JSONResponse(
                content="Passwords do not match. Please try again.", status_code=400
            )

        # Ensure the new password meets strength requirements
        if (
            len(password) < 8
            or not any(char.isupper() for char in password)
            or not any(char.isdigit() for char in password)
            or not any(char in "!@#$%^&*()_+" for char in password)
        ):
            return JSONResponse(
                content="Password does not meet strength requirements. It must be at least 8 characters long, contain at least one uppercase letter, one digit, and one special character.",
                status_code=400,
            )

        # Check if the email and token are valid
        result = user.find_one(db, email=email, email_verify_token=token)

        if not result:
            return JSONResponse(
                content="Invalid email or token. Please try again.", status_code=400
            )

        # Check if the token has expired
        if result.email_verify_expired_at:
            email_expiry = result.email_verify_expired_at.replace(
                tzinfo=timezone.utc
            ).strftime("%Y%m%d%H%I")
            today = datetime.now(timezone.utc).strftime("%Y%m%d%H%I")
            if email_expiry < today:
                return JSONResponse(
                    content="Token has expired. Please request a new password reset.",
                    status_code=400,
                )
        else:
            return JSONResponse(
                content="Verification Failed! Token has expired. Please request a new verification email.",
                status_code=400,
            )

        # Update the user's password
        hashed_password = hash_password(
            password
        )  # Ensure you have a hash_password function
        # Update the user's email_verified_at field
        result.email_verify_token = None
        result.email_verify_expired_at = None
        result.password = hashed_password
        db.commit()  # Commit the changes to the database
        db.refresh(result)  # Refresh the instance with updated data

        return JSONResponse(
            content="Password reset successfully! You may now log in with your new password."
        )

    except ValidationError as e:
        # If a Pydantic validation error occurs, return a 400 error with details
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"detail": e.errors()}
        )

    except HTTPException as http_exc:
        # Re-raise known HTTP exceptions so FastAPI can handle them appropriately
        raise http_exc

    except Exception as e:
        # Handle any unexpected errors
        db.rollback()  # Rollback the changes in case of an unexpected error
        print(f"Unhandled exception: {e}")
        auth_logger.error(f"An error occurred while reset password: {e}")
        handle_router_exception(e)
