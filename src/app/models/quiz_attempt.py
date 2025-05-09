from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.app.models import Base


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    score = Column(Integer, nullable=True)
    total_questions = Column(Integer, nullable=True)
    correct_answers = Column(Integer, nullable=True)

    started_at = Column(DateTime, default=func.now(), nullable=False)
    submitted_at = Column(DateTime, nullable=True)

    # Relationships
    quiz = relationship("Quiz", back_populates="quiz_attempts", foreign_keys=[quiz_id])
    user = relationship("User", back_populates="quiz_attempts", foreign_keys=[user_id])
    attempt_answers = relationship(
        "AttemptAnswer", back_populates="quiz_attempt", cascade="all, delete-orphan"
    )
