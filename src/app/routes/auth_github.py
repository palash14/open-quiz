from fastapi import APIRouter, HTTPException, Request, status, Depends
from typing import Annotated, Optional
from starlette.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from crud import user
from config import settings
from database import get_db, get_field_value
from utils.jwt import create_jwt_token, get_client_ip, get_user_agent
from datetime import datetime, timezone, timedelta
from routers import handle_exception
from custom_logger import create_logger
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from crud.user_token import create_user_token

auth_github_logger = create_logger("auth_github_logger", "routers_auth_github.log")

# Google OAuth settings
GITHUB_CLIENT_ID = settings.GITHUB_CLIENT_ID
GITHUB_CLIENT_SECRET = settings.GITHUB_CLIENT_SECRET
GITHUB_REDIRECT_URI = settings.GITHUB_REDIRECT_URI

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


# Configure OAuth with GitHub credentials
config = Config(environ={})
oauth = OAuth(config)
oauth.register(
    name="github",
    client_id=GITHUB_CLIENT_ID,
    client_secret=GITHUB_CLIENT_SECRET,
    authorize_url="https://github.com/login/oauth/authorize",
    access_token_url="https://github.com/login/oauth/access_token",
    client_kwargs={"scope": "user:email"},
)


@router.get("/github/login")
async def login_with_github(request: Request):
    """Redirect the user to GitHub's login page."""
    try:
        redirect_uri = GITHUB_REDIRECT_URI
        return await oauth.github.authorize_redirect(request, redirect_uri)
    except Exception as e:
        auth_github_logger.error(f"Error during GitHub login redirect: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GitHub login failed",
        )


@router.get("/github/callback")
async def auth_github_callback(
    request: Request, db: Annotated[Session, Depends(get_db)]
):
    """Handle the callback from GitHub after successful login."""
    try:
        # Fetch access token
        token = await oauth.github.authorize_access_token(request)
        # Get user information from GitHub
        user_info = await oauth.github.get("https://api.github.com/user", token=token)
        user_data = user_info.json()

        # Optionally, fetch user's email if needed
        email_info = await oauth.github.get(
            "https://api.github.com/user/emails", token=token
        )
        email_data = email_info.json()

        # Extract user information
        username = user_data.get("login")  # GitHub username
        name = user_data.get("name") or username

        email = (
            email_data[0]["email"] if email_data else None
        )  # First email (if available)
        # Log user data for debugging (remove in production)

        auth_github_logger.info(f"user_info: {user_data}, emails: {email}")

        user_data = {
            "email": email,
            "name": name,
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

        url = settings.FRONTEND_URL + "/githubSignIn?token=" + access_token
        return RedirectResponse(url)

    except Exception as e:
        db.rollback()
        # Log the exception (in real-world application, use proper logging)
        print(f"Unhandled exception: {e}")
        auth_github_logger.error(f"Unhandled exception: {e}")
        handle_exception(e)
