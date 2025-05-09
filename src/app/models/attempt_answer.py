from sqlalchemy import Column, Boolean, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.app.models import Base


class AttemptAnswer(Base):
    __tablename__ = "attempt_answers"

    id = Column(Integer, primary_key=True, index=True)
    quiz_attempt_id = Column(Integer, ForeignKey("quiz_attempts.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    selected_choice_id = Column(Integer, ForeignKey("choices.id"), nullable=True)

    is_correct = Column(Boolean, nullable=True)  # True/False after evaluation

    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    quiz_attempt = relationship(
        "QuizAttempt", back_populates="attempt_answers", foreign_keys=[quiz_attempt_id]
    )
    question = relationship("Question", foreign_keys=[question_id])
    choice = relationship("Choice", foreign_keys=[selected_choice_id])
