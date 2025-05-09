# src/app/routes/quiz.py
from fastapi import APIRouter
# from src.app.schemas.quiz import QuizCreate, QuizOut

router = APIRouter(prefix="/quizzes", tags=["Quizzes"])

@router.post("/")
def create_quiz():
    """
    Create a new quiz.
    """
    pass

