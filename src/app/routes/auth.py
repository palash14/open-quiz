from typing import Annotated
from fastapi import APIRouter, Form, Depends, status, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from urllib.parse import unquote
from sqlalchemy.orm import Session
from pydantic import BaseModel, ValidationError
from datetime import datetime, timezone, timedelta
from cryptography.fernet import Fernet
from database import get_db, get_field_value
from routers import handle_exception
from schemas.user import UserCreate, UserResponse
from crud import user
from user_tasks import send_verification_email_task, send_forgot_email_task
from utils import create_redirect_uri
from utils.hashing import verify_password, hash_password
from utils.jwt import create_jwt_token, decode_jwt_token, get_client_ip, get_user_agent

from cryptography.fernet import Fernet
from config import settings
from validators.auth_validator import RegistrationFormValidator, ForgotPasswordValidator
from models.user import generate_uuid
from jinja2 import Template
from crud.user import find_one
from custom_logger import create_logger
from crud.user_token import create_user_token

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

        # Get the encryption key from the environment variable
        encryption_key = settings.CRYPTO_SECRET_KEY

        # Check if the key was loaded successfully
        if not encryption_key:
            raise ValueError(
                "Encryption key not found. Please set 'CRYPTO_SECRET_KEY' in your .env file."
            )

        cipher_suite = Fernet(encryption_key)
        encrypted_token = cipher_suite.encrypt(new_user.email_verify_token.encode())

        # Generate email verification link
        verification_link = create_redirect_uri(
            redirect_uri=settings.BACKEND_URL + "/auth/email-verify",
            additional_params={
                "email": validated_data.user.email,
                "token": encrypted_token,
            },
        )

        # Queue the email verification task
        send_verification_email_task.apply_async(
            args=[new_user.email, verification_link], queue="email_queue"
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
        handle_exception(e)


# HTML template for email verification
EMAIL_VERIFY_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Email Verification</title>
</head>
<body>
    <h1>Email Verification</h1>
    {% if error %}
        <p style="color: red;">{{ error }}</p>
    {% endif %}
    <form action="/auth/verify-email" method="post">
        <label for="email">Enter your email address:</label><br><br>
        <input type="email" id="email" name="email" value="{{ email }}" required><br><br>
        <input type="hidden" name="token" value="{{ token }}">
        <input type="submit" value="Verify Email">
    </form>
</body>
</html>
"""


@router.get("/email-verify", response_class=HTMLResponse)
def email_verify(
    request: Request, email: str, token: str, db: Annotated[Session, Depends(get_db)]
):
    """
    Handle GET requests for verifying an email using a token.

    :param request: The HTTP request object.
    :param token: The email verification token.
    :param db: The SQLAlchemy session.
    :return: HTML page to verify the user's email address.
    """

    # Decoding the email and token
    decoded_email = unquote(email) if email else None
    decoded_token = unquote(token) if token else None

    # Get the encryption key from the environment variable
    encryption_key = settings.CRYPTO_SECRET_KEY

    # Check if the key was loaded successfully
    if not encryption_key:
        raise ValueError(
            "Encryption key not found. Please set 'CRYPTO_SECRET_KEY' in your .env file."
        )

    cipher_suite = Fernet(encryption_key)

    decrypted_token = cipher_suite.decrypt(decoded_token).decode()

    # Check if the token exists in the database and is valid
    user = find_one(db, email=decoded_email, email_verify_token=decrypted_token)

    if not user:
        return HTMLResponse(
            content="<h1>Invalid or expired token.</h1>", status_code=400
        )

    # Check if the token has expired (assuming you have an expiration date in the database)
    if user.email_verify_expired_at:
        email_expiry = user.email_verify_expired_at.replace(
            tzinfo=timezone.utc
        ).strftime("%Y%m%d%H%I")
        today = datetime.now(timezone.utc).strftime("%Y%m%d%H%I")
        if email_expiry < today:
            raise HTTPException(status_code=400, detail="Token has expired!")

    else:
        raise HTTPException(status_code=400, detail="Token has expired. ")

    # Render the HTML form where the user can enter their email address
    template = Template(EMAIL_VERIFY_TEMPLATE)
    return HTMLResponse(template.render(token=decoded_token, email=decoded_email))


@router.post(
    "/verify-email",
    summary="Verify user's email address",
    description="This endpoint verifies a user's email address.",
    response_class=HTMLResponse,
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
        # Get the encryption key from the environment variable
        encryption_key = settings.CRYPTO_SECRET_KEY

        # Check if the key was loaded successfully
        if not encryption_key:
            raise ValueError(
                "Encryption key not found. Please set 'CRYPTO_SECRET_KEY' in your .env file."
            )

        cipher_suite = Fernet(encryption_key)

        decrypted_token = cipher_suite.decrypt(token).decode()
        result = user.find_one(db, email=email, email_verify_token=decrypted_token)

        if not result:
            return HTMLResponse(
                content="<h1>Verification Failed</h1><p>Invalid email or token. Please try again.</p>",
                status_code=400,
            )

        if result.email_verified_at is not None:
            return HTMLResponse(
                content="<h1>Email address already verified.</h1>", status_code=400
            )

        # Check if the token has expired
        if result.email_verify_expired_at:
            email_expiry = result.email_verify_expired_at.replace(
                tzinfo=timezone.utc
            ).strftime("%Y%m%d%H%I")
            today = datetime.now(timezone.utc).strftime("%Y%m%d%H%I")
            if email_expiry < today:
                return HTMLResponse(
                    content="<h1>Verification Failed</h1><p>Token has expired. Please request a new verification email.</p>",
                    status_code=400,
                )
        else:
            return HTMLResponse(
                content="<h1>Verification Failed</h1><p>Token has expired. Please request a new verification email.</p>",
                status_code=400,
            )

        # Update the user's email_verified_at field
        result.email_verified_at = datetime.now().replace(tzinfo=timezone.utc)
        result.email_verify_token = None  # Invalidate the token after verification
        result.email_verify_expired_at = None
        db.commit()  # Commit the changes to the database
        db.refresh(result)  # Refresh the instance with updated data
        url = settings.FRONTEND_URL + "/thankYou"
        return RedirectResponse(url)

    except HTTPException as http_exc:
        # Re-raise known HTTP exceptions
        raise http_exc

    except Exception as e:
        db.rollback()  # Rollback any changes if an error occurs
        # Log the exception (in a real-world application, use proper logging)
        print(f"Unhandled exception: {e}")
        auth_logger.error(f"An error occurred while verify email: {e}")
        handle_exception(e)


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
        handle_exception(e)


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

        # Get the encryption key from the environment variable
        encryption_key = settings.CRYPTO_SECRET_KEY

        # Check if the key was loaded successfully
        if not encryption_key:
            raise ValueError(
                "Encryption key not found. Please set 'CRYPTO_SECRET_KEY' in your .env file."
            )

        cipher_suite = Fernet(encryption_key)
        encrypted_token = cipher_suite.encrypt(reset_token.encode())

        # Create reset link
        reset_link = create_redirect_uri(
            redirect_uri=settings.FRONTEND_URL + "/resetPassword",
            additional_params={"email": request.email, "token": encrypted_token},
        )
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
        handle_exception(e)


# HTML template for password RESET
PASSWORD_RESET_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Password Reset</title>
</head>
<body>
    <h1>Password Reset</h1>
    {% if error %}
        <p style="color: red;">{{ error }}</p>
    {% endif %}
    <form action="/auth/reset-password" method="post" autocomplete="off">
        <label for="email">Enter your email address:</label><br><br>
        <input type="email" id="email" name="email" value="{{ email }}" required autocomplete="off"><br><br>
        
        <label for="password">Enter new password:</label><br><br>
        <input type="password" id="password" name="password" value="" required autocomplete="new-password"><br><br>

        <label for="confirm_password">Confirm new password:</label><br><br>
        <input type="password" id="confirm_password" name="confirm_password" value="" required autocomplete="new-password"><br><br>
        
        <input type="hidden" name="token" value="{{ token }}">
        <input type="submit" value="Reset Password">
    </form>
</body>
</html>
"""


@router.get("/reset-password", response_class=HTMLResponse)
def reset_password(
    request: Request, email: str, token: str, db: Annotated[Session, Depends(get_db)]
):
    """
    Handle GET requests for reset password using a token.

    :param request: The HTTP request object.
    :param token: The email verification token.
    :param db: The SQLAlchemy session.
    :return: HTML page to reset user password.
    """

    # Get the encryption key from the environment variable
    encryption_key = settings.CRYPTO_SECRET_KEY

    # Check if the key was loaded successfully
    if not encryption_key:
        raise ValueError(
            "Encryption key not found. Please set 'CRYPTO_SECRET_KEY' in your .env file."
        )

    cipher_suite = Fernet(encryption_key)

    decrypted_token = cipher_suite.decrypt(token).decode()

    # Check if the token exists in the database and is valid
    user = find_one(db, email=email, email_verify_token=decrypted_token)

    if not user:
        return HTMLResponse(
            content="<h1>Invalid or expired token.</h1>", status_code=400
        )

    # Check if the token has expired (assuming you have an expiration date in the database)
    if user.email_verify_expired_at:
        email_expiry = user.email_verify_expired_at.replace(
            tzinfo=timezone.utc
        ).strftime("%Y%m%d%H%I")
        today = datetime.now(timezone.utc).strftime("%Y%m%d%H%I")
        if email_expiry < today:
            raise HTTPException(status_code=400, detail="Token has expired.")

    else:
        raise HTTPException(status_code=400, detail="Token has expired.")

    # Render the HTML form where the user can enter their email address
    template = Template(PASSWORD_RESET_TEMPLATE)
    return HTMLResponse(template.render(token=token, email=email))


@router.post(
    "/reset-password",
    summary="Reset user password",
    description="This endpoint resets the user's password using the provided token.",
    response_class=HTMLResponse,
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
            return HTMLResponse(
                content="Passwords do not match. Please try again.", status_code=400
            )

        # Ensure the new password meets strength requirements
        if (
            len(password) < 8
            or not any(char.isupper() for char in password)
            or not any(char.isdigit() for char in password)
            or not any(char in "!@#$%^&*()_+" for char in password)
        ):
            return HTMLResponse(
                content="Password does not meet strength requirements. It must be at least 8 characters long, contain at least one uppercase letter, one digit, and one special character.",
                status_code=400,
            )

        # Get the encryption key from the environment variable
        encryption_key = settings.CRYPTO_SECRET_KEY

        # Check if the key was loaded successfully
        if not encryption_key:
            raise ValueError(
                "Encryption key not found. Please set 'CRYPTO_SECRET_KEY' in your .env file."
            )

        cipher_suite = Fernet(encryption_key)

        decrypted_token = cipher_suite.decrypt(token).decode()

        # Check if the email and token are valid
        result = user.find_one(db, email=email, email_verify_token=decrypted_token)

        if not result:
            return HTMLResponse(
                content="Invalid email or token. Please try again.", status_code=400
            )

        # Check if the token has expired
        if result.email_verify_expired_at:
            email_expiry = result.email_verify_expired_at.replace(
                tzinfo=timezone.utc
            ).strftime("%Y%m%d%H%I")
            today = datetime.now(timezone.utc).strftime("%Y%m%d%H%I")
            if email_expiry < today:
                return HTMLResponse(
                    content="Token has expired. Please request a new password reset.",
                    status_code=400,
                )
        else:
            return HTMLResponse(
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

        return HTMLResponse(
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
        handle_exception(e)