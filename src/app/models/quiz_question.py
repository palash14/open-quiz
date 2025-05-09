# /src/app/models/quiz_question.py
from sqlalchemy import Column, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.app.models import Base


class QuizQuestion(Base):
    __tablename__ = "quiz_questions"

    id = Column(Integer, primary_key=True, index=True)
    quiz_id = Column(Integer, ForeignKey("quizzes.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)

    # Optional ordering field
    position = Column(Integer, nullable=True)  # order of the questions

    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    quiz = relationship("Quiz", back_populates="quiz_questions", foreign_keys=[quiz_id])
    question = relationship("Question", foreign_keys=[question_id])
