from sqlalchemy import Column, String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.app.models import Base


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    total_questions = Column(Integer, nullable=True)

    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="quizzes", foreign_keys=[user_id])
    quiz_questions = relationship(
        "QuizQuestion", back_populates="quiz", cascade="all, delete-orphan"
    )
    quiz_attempts = relationship(
        "QuizAttempt", back_populates="quiz", cascade="all, delete-orphan"
    )
