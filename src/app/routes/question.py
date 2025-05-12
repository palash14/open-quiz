# src/app/routes/quiz.py
from typing import Annotated
from fastapi import APIRouter, Depends, status, status
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.schemas.question import QuestionCreate, QuestionResponse
from src.app.services.question_service import QuestionService
from src.app.core.logger import create_logger
from src.app.utils.exceptions import handle_router_exception

router = APIRouter(
    prefix="/questions",
    tags=["Questions"],
    responses={404: {"description": "Not found"}},
)

logger = create_logger("question", "routers_question.log")


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
    try:
        service = QuestionService(db)
        payload = request.copy(update={"user_id": 1})
        question = service.create(payload)

        db.commit()
        return QuestionResponse.model_validate(question)
    except Exception as e:
        logger.error(e)
        db.rollback()
        handle_router_exception(e)
