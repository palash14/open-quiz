# File: src/app/utils/jwt.py
import jwt
from fastapi import Request, Depends, HTTPException, status
from jwt.exceptions import InvalidTokenError
from datetime import datetime, timedelta, timezone
from typing import Union, Tuple
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from src.app.models.user_token import UserToken
from src.app.core.config import settings
from src.app.models.user import User, UserStatusEnum
from src.app.core.database import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


class TokenData(BaseModel):
    email: Union[str, None] = None


def create_jwt_token(subject: str, expires_delta: timedelta = None) -> Tuple[str, str]:
    """
    Create a JWT token.

    :param subject: The subject (user) for whom the token is created.
    :param expires_delta: Optional timedelta for token expiration.
    :return: A tuple containing the access token and refresh token.
    """
    now = datetime.now(timezone.utc)

    # Access token (short-lived, e.g., 15 minutes)
    access_token_expire = now + (
        expires_delta or timedelta(minutes=int(settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    )
    access_token_payload = {
        "exp": access_token_expire,
        "sub": subject,
        "type": "access",
    }
    access_token = jwt.encode(
        access_token_payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )

    # Refresh token (long-lived, e.g., 7 days)
    refresh_token_expire = now + (
        expires_delta or timedelta(days=int(settings.REFRESH_TOKEN_EXPIRE_DAYS))
    )
    refresh_token_payload = {
        "exp": refresh_token_expire,
        "sub": subject,
        "type": "refresh",
    }
    refresh_token = jwt.encode(
        refresh_token_payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )

    return access_token, refresh_token


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """
    Retrieve the current user from the JWT token.

    :param token: The JWT token from the request header.
    :param db: The SQLAlchemy session.
    :return: The User object if the token is valid.
    :raises HTTPException: If token is invalid, expired, or user not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode the JWT token
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        email: str = payload.get("sub")

        # Ensure email is present in payload
        if email is None:
            raise credentials_exception

        # Create TokenData instance
        token_data = TokenData(email=email)

    except InvalidTokenError:
        raise credentials_exception

    # Fetch the user using the email
    user_instance = User.find_one(db, email=token_data.email)

    if not user_instance:
        raise credentials_exception

    # Ensure the user status is active
    if user_instance.status != UserStatusEnum.active:
        message = f"Your account is {user_instance.status.value}"
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)

    token_record = db.query(UserToken).filter_by(access_token=token).first()
    if not token_record:
        raise HTTPException(status_code=404, detail="Token not found")

    # Get the current time in UTC
    current_time = datetime.now(timezone.utc)

    # Convert token_record.expired_at to a timezone-aware datetime
    if token_record.expired_at:
        expired_at_aware = token_record.expired_at.replace(tzinfo=timezone.utc)
    else:
        raise HTTPException(status_code=400, detail="Expired at timestamp not found")

    # Check if the token is expired
    if current_time > expired_at_aware:
        raise HTTPException(status_code=401, detail="Token has expired")

    return user_instance


def generate_password_reset_token(user_id: int) -> str:
    token_data = {
        "sub": user_id,
        "exp": datetime.now() + timedelta(hours=1),  # Token expires in 1 hour
    }
    return jwt.encode(token_data, settings.SECRET_KEY, algorithm="HS256")


def verify_password_reset_token(token: str) -> int:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        return 0  # Token has expired
    except jwt.InvalidTokenError:
        return 0  # Invalid token


def decode_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")


def get_client_ip(request: Request) -> str:
    """Get the client's IP address."""
    ip = request.client.host
    # Handle case where the app is behind a proxy or load balancer
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # Return the first IP address in the list if "X-Forwarded-For" header exists
        ip = forwarded_for.split(",")[0].strip()
    return ip


def get_user_agent(request: Request) -> str:
    """Get the User-Agent from the request."""
    return request.headers.get("user-agent", "unknown")


def validate_and_revoke_token(token: str, db: Session):
    """
    Validate the token and revoke or expire it.
    """
    try:
        # Fetch the token record from the database
        token_record = db.query(UserToken).filter_by(access_token=token).first()
        if not token_record:
            raise HTTPException(status_code=404, detail="Token not found")

        # Mark the token as revoked
        token_record.expired_at = datetime.now()
        token_record.updated_at = datetime.now()
        db.commit()
        return {"message": "Token revoked successfully"}

    except jwt.ExpiredSignatureError:
        # Token is expired, mark it as expired in the database
        token_record = db.query(UserToken).filter_by(access_token=token).first()
        if token_record:
            token_record.expired_at = datetime.now()
            token_record.updated_at = datetime.now()
            db.commit()
        raise HTTPException(status_code=401, detail="Token has expired")

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def verify_access_token(token: str) -> bool:
    try:
        jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return True
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False

def create_user_token(db: Session, user_id: int, access_token: str, refresh_token: str, ip: str, user_agent: str, expired_at: datetime):
    now = datetime.now()
    new_token = UserToken(
        user_id=user_id,
        access_token=access_token,
        refresh_token=refresh_token,
        ip=ip,
        user_agent=user_agent,
        expired_at=expired_at,
        created_at=now,
        updated_at=now
    )
    db.add(new_token)
    db.commit()
    db.refresh(new_token)
    return new_token
