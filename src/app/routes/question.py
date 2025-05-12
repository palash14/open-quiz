# src/app/routes/quiz.py
from typing import Annotated, List
from fastapi import APIRouter, Depends, status, HTTPException, status
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.schemas.question import QuestionCreate, QuestionResponse


router = APIRouter(
    prefix="/questions",
    tags=["Questions"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/",
    summary="Create Question",
    description="Create a new Question.",
    response_model=QuestionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_quiz(
    request: QuestionCreate,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Create a new quiz.
    """
    pass
