from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Enum,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.app.models import Base
from enum import Enum as PyEnum


class UserStatusEnum(PyEnum):
    """
    Enumeration for the possible statuses of a user:
    - active: User is currently active.
    - inactive: User is currently inactive.
    - blocked: User is blocked from accessing the platform.
    """

    active = "active"
    inactive = "inactive"
    blocked = "blocked"


class UserTypeEnum(PyEnum):
    is_admin = "admin"
    is_user = "user"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    email = Column(String(320), unique=True, nullable=False)
    phone_no = Column(String(15), nullable=True)
    dial_code = Column(String(5), nullable=True)
    password = Column(String, nullable=False)
    email_verified_at = Column(DateTime, nullable=True)
    email_verify_token = Column(String, nullable=True)
    email_verify_expired_at = Column(DateTime, nullable=True)
    status = Column(Enum(UserStatusEnum), default=UserStatusEnum.active, nullable=False)
    user_type = Column(Enum(UserTypeEnum), default=UserTypeEnum.is_user, nullable=False)

    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)

    # One-to-many relationship with the Question model
    questions = relationship("Question", back_populates="user")
    quizzes = relationship("Quiz", back_populates="user")
    quiz_attempts = relationship(
        "QuizAttempt", back_populates="user", cascade="all, delete-orphan"
    )
    # Unique constraint on the combination of phone_no and dial_code
    __table_args__ = (
        UniqueConstraint("phone_no", "dial_code", name="uq_phone_no_dial_code"),
    )
