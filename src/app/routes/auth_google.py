from fastapi import APIRouter, HTTPException, Request, status, Depends
from typing import Annotated, Optional
from starlette.responses import RedirectResponse
from requests_oauthlib import OAuth2Session
from sqlalchemy.orm import Session
from pydantic import BaseModel
from crud import user
from config import settings
from database import get_db, get_field_value
from utils.jwt import create_jwt_token, get_client_ip, get_user_agent
from datetime import datetime, timezone, timedelta
from routers import handle_exception
from custom_logger import create_logger
from crud.user_token import create_user_token

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


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: str
    name: str
    phone_no: Optional[str] = None
    dial_code: Optional[str] = None
    password: str
    email_verified_at: Optional[datetime] = None
    email_verify_token: Optional[str] = None
    email_verify_expired_at: Optional[datetime] = None
    status: str


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
def auth_google_callback(request: Request, db: Annotated[Session, Depends(get_db)]):
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
            raise HTTPException(
                status_code=400, detail="Failed to fetch user info from Google"
            )

        user_info = response.json()
        email = user_info.get("email")
        full_name = user_info.get("name")

        user_data = {
            "email": email,
            "name": full_name,
            "phone_no": None,
            "dial_code": None,
            "password": datetime.now(timezone.utc).strftime("%Y%m%d%H%I"),
            "email_verified_at": datetime.today(),
            "email_verify_token": None,
            "email_verify_expired_at": None,
            "status": "active",
        }

        existing_user_by_email = get_field_value(db, "users", "email", email)

        # Register or login the user in the mock database
        if existing_user_by_email:
            # Create JWT token
            access_token, refresh_token = create_jwt_token(subject=email)
            user_id = existing_user_by_email.id
        else:
            # Convert the dictionary to a Pydantic model instance
            user_create = UserCreate(**user_data)

            # Create a new user in the mock database
            user_new_data = user.create(db, None, user_create)
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

        url = settings.FRONTEND_URL + "/googleSignIn?token=" + access_token
        return RedirectResponse(url)

    except Exception as e:
        db.rollback()
        # Log the exception (in real-world application, use proper logging)
        print(f"Unhandled exception: {e}")
        auth_google_logger.error(f"Unhandled exception: {e}")
        handle_exception(e)