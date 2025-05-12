# src/app/routes/quiz.py
from fastapi import APIRouter


router = APIRouter(
    prefix="/quizzes",
    tags=["Quizzes"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/",
)
def create_quiz():
    """
    Create a new quiz.
    """
    pass
