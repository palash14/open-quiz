from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    ForeignKey,
    Enum,
    Boolean,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.app.models import Base
from enum import Enum as PyEnum


class QuestionStatusEnum(PyEnum):
    active = "active"
    rejected = "rejected"
    draft = "draft"


class QuestionDifficultyEnum(PyEnum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class QuestionTypeEnum(PyEnum):
    multiple_choice = "multiple_choice"  # Multiple correct answers
    boolean = "boolean"  # Boolean (true/false)


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)

    question = Column(String(200), unique=True, nullable=False)
    question_type = Column(
        Enum(QuestionTypeEnum), default=QuestionTypeEnum.multiple_choice, nullable=False
    )
    status = Column(
        Enum(QuestionStatusEnum), default=QuestionStatusEnum.draft, nullable=False
    )
    difficulty = Column(
        Enum(QuestionDifficultyEnum),
        default=QuestionDifficultyEnum.medium,
        nullable=False,
    )
    is_published = Column(Boolean, default=False, nullable=False)
    review_comment = Column(String(200), nullable=True)
    explanation = Column(Text, nullable=True)
    references = Column(Text, nullable=True)

    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="questions", foreign_keys=[user_id])
    category = relationship(
        "Category", back_populates="questions", foreign_keys=[category_id]
    )
    choices = relationship(
        "Choice", back_populates="question", cascade="all, delete-orphan"
    )
