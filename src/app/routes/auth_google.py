# File: src/app/routes/auth_google.py
from fastapi import APIRouter, Request, Depends
from typing import Annotated
from starlette.responses import RedirectResponse
from requests_oauthlib import OAuth2Session
from sqlalchemy.orm import Session
from uuid import uuid4
from src.app.core.config import settings
from src.app.core.database import get_db
from src.app.core.config import settings
from src.app.utils.jwt import (
    create_jwt_token,
    get_client_ip,
    get_user_agent,
    create_user_token,
)
from datetime import datetime, timezone, timedelta
from src.app.services.user_service import UserService
from src.app.core.logger import create_logger
from src.app.schemas.auth import (
    UserCreate,
    Token,
)

auth_google_logger = create_logger("auth_google_logger", "routers_auth_google.log")

# Google OAuth settings
GOOGLE_CLIENT_ID = settings.GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET = settings.GOOGLE_CLIENT_SECRET
GOOGLE_REDIRECT_URI = settings.GOOGLE_REDIRECT_URI
GOOGLE_AUTHORIZATION_BASE_URL = settings.GOOGLE_AUTHORIZATION_BASE_URL
GOOGLE_TOKEN_URL = settings.GOOGLE_TOKEN_URL
SCOPE2 = settings.GOOGLE_SCOPE
GOOGLE_SCOPE = SCOPE2.split(",")

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={404: {"description": "Not found"}},
)
 


@router.get("/google/login")
def login_with_google():
    """Redirects user to Google's OAuth login page."""

    google = OAuth2Session(
        GOOGLE_CLIENT_ID, redirect_uri=GOOGLE_REDIRECT_URI, scope=GOOGLE_SCOPE
    )
    authorization_url, _ = google.authorization_url(
        GOOGLE_AUTHORIZATION_BASE_URL, access_type="offline"
    )
    return RedirectResponse(url=authorization_url)


@router.get("/google/callback")
def auth_google_callback(request: Request, db: Annotated[Session, Depends(get_db)]) -> Token:
    """Handles Google OAuth callback and extracts user information."""
    try:
        google = OAuth2Session(
            GOOGLE_CLIENT_ID, redirect_uri=GOOGLE_REDIRECT_URI, scope=GOOGLE_SCOPE
        )
        google.fetch_token(
            GOOGLE_TOKEN_URL,
            client_secret=GOOGLE_CLIENT_SECRET,
            authorization_response=str(request.url),
        )

        # Use token to get user information
        response = google.get("https://www.googleapis.com/oauth2/v1/userinfo")
        if response.status_code != 200:
            raise ValueError("Failed to fetch user info from Google")

        user_info = response.json()
        email = user_info.get("email")
        full_name = user_info.get("name")

        user_service = UserService(db)

        existing_user_by_email = user_service.find_one(email=email)

        # Register or login the user in the mock database
        if existing_user_by_email:
            # Create JWT token
            access_token, refresh_token = create_jwt_token(subject=email)
            user_id = existing_user_by_email.id
        else:
            user_create = UserCreate(
                email=email,
                name=full_name,
                password=str(uuid4()),
                email_verified_at=datetime.now(),
                email_verify_token=None,
                email_verify_expired_at=None,
                status="active",
            )             

            # Create a new user in the mock database
            user_new_data = user_service.create(user_create)
            db.commit()
            user_id = user_new_data.id
            access_token, refresh_token = create_jwt_token(subject=email)

        create_user_token(
            db=db,
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            ip=get_client_ip(request),
            user_agent=get_user_agent(request),
            expired_at=datetime.now()
            + timedelta(minutes=int(settings.ACCESS_TOKEN_EXPIRE_MINUTES)),
        )

        return Token(access_token=access_token, refresh_token=refresh_token)

    except Exception as e:
        db.rollback()
        auth_google_logger.error(f"Unhandled exception: {e}")
        raise e
