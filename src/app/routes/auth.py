from typing import Annotated, Union
from fastapi import APIRouter, Depends, status, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from src.app.core.database import get_db
from src.app.utils.exceptions import ValidationException
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
from src.app.schemas.auth import (
    EmailVerifyValidator,
    ForgotPasswordValidator, 
    ResetPasswordValidator,
    RefreshTokenRequest,
    AuthRouterResponse,
    RegistrationResponse, 
    Token
)
from src.app.services.user_service import UserService
from src.app.core.logger import create_logger
from src.app.tasks.queue_task import send_verification_email_task, send_forgot_email_task

auth_logger = create_logger("auth_logger", "route_auth.log")

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/register",
    summary="Register a new user",
    description="This endpoint registers a new user in the system.",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    request: UserCreate,
    db: Annotated[Session, Depends(get_db)],
) -> Union[RegistrationResponse, JSONResponse] :
    """
    Handles the registration of a user and sends an email verification link.

    :param request: The registration form containing user data.
    :param db: The SQLAlchemy session dependency.
    :return: A structured response indicating the success of the registration.
    :raises HTTPException: If a database error occurs during registration.
    """
    try:         

        user_service = UserService(db)

        # Check if the email already exists
        existing_user_by_email = user_service.find_one(
            email=request.email
        )

        if existing_user_by_email:
            raise ValidationException("User with this email already exists")
        # Create user records
        new_user = user_service.create(request)

        # Generate email verification token
        email_otp = new_user.email_verify_token

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

    except Exception as e:
        db.rollback()
        auth_logger.error(f"An error occurred while creating a user: {e}")
        raise e


@router.post(
    "/verify-email",
    summary="Verify user's email address",
    description="This endpoint verifies a user's email address.",
    response_class=JSONResponse,
)
def verify_email(
    db: Annotated[Session, Depends(get_db)],
    request: EmailVerifyValidator
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
        user_service = UserService(db)
        result = user_service.find_one(email=request.email, email_verify_token=request.token)

        if not result:
            raise ValidationException("Invalid email or token. Please try again.")

        if result.email_verified_at is not None:
            raise ValidationException("Email address already verified.")

        # Check if the token has expired
        if result.email_verify_expired_at:
            email_expiry = result.email_verify_expired_at.replace(
                tzinfo=timezone.utc
            ).strftime("%Y%m%d%H%I")
            today = datetime.now(timezone.utc).strftime("%Y%m%d%H%I")
            if email_expiry < today:
                raise ValidationException(
                    "Token has expired. Please request a new verification email."
                )
        else:
            raise ValidationException("Token has expired. Please request a new verification email.")
            

        # Update the user's email_verified_at field
        result.email_verified_at = datetime.now().replace(tzinfo=timezone.utc)
        result.email_verify_token = None  # Invalidate the token after verification
        result.email_verify_expired_at = None
        db.commit()  # Commit the changes to the database
        db.refresh(result)  # Refresh the instance with updated data
        return JSONResponse(
            content="Email address verified successfully.", status_code=200
        ) 

    except Exception as e:
        db.rollback()  # Rollback any changes if an error occurs
        auth_logger.error(f"An error occurred while verify email: {e}")
        raise e


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
        user_service = UserService(db)
        user_data = user_service.find_one(email=form_data.username)

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
        auth_logger.error(f"An error occurred while login: {e}")
        raise e


@router.post(
    "/refresh-token",
    summary="Login and get JWT token",
    description="This endpoint logs in a user and returns a JWT token.",
    response_model=Token,
    status_code=status.HTTP_200_OK,
)
async def refresh_access_token(request: RefreshTokenRequest):
    try:
        payload = decode_jwt_token(request.refresh_token)
        if payload.get("type") != "refresh":
            raise ValidationException("Invalid token type")

        new_access_token, refresh_token = create_jwt_token(subject=payload["sub"])
        return Token(access_token=new_access_token, refresh_token=refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post(
    "/forgot-password",
    summary="Send a password reset email",
    description="This endpoint sends a password reset email to the user.",
    response_model=AuthRouterResponse,
    status_code=status.HTTP_200_OK,
)
def forgot_password(
    request: ForgotPasswordValidator,
    db: Annotated[Session, Depends(get_db)],
) -> AuthRouterResponse:
    """
    Handles the forgot password request. It generates a reset token and sends an email.

    :param request: The form containing the user's email.
    :param db: The SQLAlchemy session dependency.
    :return: A structured response indicating the success of the operation.
    :raises HTTPException: If the user is not found.
    """
    try:
        user_service = UserService(db)
        user_data = user_service.find_one(email=request.email)
        if not user_data:
            raise ValidationException("User not found")

        # Generate password reset token
        reset_token = user_service.generate_otp()

        email_token_expired_at = datetime.today() + timedelta(1)
        # Update the user's email_verified_at field
        user_data.email_verify_token = reset_token
        user_data.email_verify_expired_at = email_token_expired_at
        db.commit()  # Commit the changes to the database
        db.refresh(user_data)  # Refresh the instance with updated data

        # Queue the password reset email task
        send_forgot_email_task.apply_async(
            args=[request.email, reset_token], queue="email_queue"
        )

        return AuthRouterResponse(
            success=True, detail="Password reset email sent successfully."
        )

    except Exception as e:
        print(f"Unhandled exception: {e}")
        auth_logger.error(f"An error occurred while forgot password: {e}")
        raise e


@router.post(
    "/reset-password",
    summary="Reset user password",
    description="This endpoint resets the user's password using the provided token.",
    response_model=AuthRouterResponse,
    status_code=status.HTTP_200_OK,
)
def reset_password(
    request: ResetPasswordValidator,
    db: Annotated[Session, Depends(get_db)], 
)-> Union[AuthRouterResponse, JSONResponse]:
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
        
        user_service = UserService(db)

        # Check if the email and token are valid
        result = user_service.find_one(email=request.email, email_verify_token=request.token)

        if not result:
            raise ValidationException("Invalid email or token. Please try again.")

        # Check if the token has expired
        if result.email_verify_expired_at:
            email_expiry = result.email_verify_expired_at.replace(
                tzinfo=timezone.utc
            ).strftime("%Y%m%d%H%I")
            today = datetime.now(timezone.utc).strftime("%Y%m%d%H%I")
            if email_expiry < today:
                raise ValidationException(
                    "Token has expired. Please request a new password reset."
                )
        else:
            raise ValidationException("Token has expired. Please request a new password reset.")
            

        # Update the user's password
        hashed_password = hash_password(
            request.password
        )  # Ensure you have a hash_password function
        # Update the user's email_verified_at field
        result.email_verify_token = None
        result.email_verify_expired_at = None
        result.password = hashed_password
        db.commit()  # Commit the changes to the database
        db.refresh(result)  # Refresh the instance with updated data

        return AuthRouterResponse(
            success=True,
            detail="Password reset successfully! You may now log in with your new password."
        ) 

    except Exception as e:
        # Handle any unexpected errors
        db.rollback()  # Rollback the changes in case of an unexpected error
        auth_logger.error(f"An error occurred while reset password: {e}")
        raise e
