from fastapi import APIRouter, HTTPException, Request, status, Depends
from typing import Annotated
from sqlalchemy.orm import Session
from uuid import uuid4
from src.app.core.database import get_db
from src.app.core.config import settings
from src.app.utils.jwt import (
    create_jwt_token,
    get_client_ip,
    get_user_agent,
    create_user_token,
)
from datetime import datetime, timezone, timedelta
from src.app.core.logger import create_logger
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from src.app.schemas.auth import (
    UserCreate,
    Token,
)
from src.app.services.user_service import UserService

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
        authorization_url = await oauth.github.authorize_redirect(request, redirect_uri)
        return authorization_url
    except Exception as e:
        auth_github_logger.error(f"Error during GitHub login redirect: {e}")
        raise e


@router.get(
    "/github/callback",
    summary="Github Callback",
    description="This endpoint logs in or registers a user via GitHub OAuth.",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
)
async def auth_github_callback(
    request: Request, db: Annotated[Session, Depends(get_db)]
) -> Token:
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
        email = next(
            (e["email"] for e in email_data if e.get("primary") and e.get("verified")),
            None,
        )
        if not email:
            raise ValueError("Verified primary email not found.")

        name = user_data.get("name") or user_data.get("login")
        user_service = UserService(db)

        auth_github_logger.info(f"user_info: {user_data}, emails: {email}")

        existing_user_by_email = user_service.find_one(email=email)

        # Register or login the user in the mock database
        if existing_user_by_email:
            # Create JWT token
            access_token, refresh_token = create_jwt_token(subject=email)
            user_id = existing_user_by_email.id
        else:
            user_create = UserCreate(
                email=email,
                name=name,
                password=str(uuid4()),
                email_verified_at=datetime.now(),
                email_verify_token=None,
                email_verify_expired_at=None,
                status="active",
            )
            new_user = user_service.create(user_create)
            db.commit()
            user_id = new_user.id
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
        auth_github_logger.error(f"Unhandled exception: {e}")
        raise e
