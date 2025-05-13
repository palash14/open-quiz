# src/app/routes/quiz.py
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.schemas.question import (
    QuestionCreate,
    QuestionResponse,
    PaginateQuestionResponse,
)
from src.app.services.question_service import QuestionService
from src.app.core.logger import create_logger
from src.app.utils.exceptions import handle_router_exception
from enum import Enum

router = APIRouter(
    prefix="/questions",
    tags=["Questions"],
    responses={404: {"description": "Not found"}},
)

logger = create_logger("question", "routers_question.log")


class SortByField(str, Enum):
    id = "id"


class SortByOrder(str, Enum):
    asc = "asc"
    desc = "desc"


@router.get(
    "/",
    summary="Get Questions",
    description="Get all Questions.",
    response_model=PaginateQuestionResponse,
    status_code=status.HTTP_200_OK,
)
def get_questions(
    db: Annotated[Session, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort_by: Optional[str] = Query(SortByField.id),
    sort_order: Optional[str] = Query(SortByOrder.desc),
):
    try:
        service = QuestionService(db)
        paginated_questions = service.paginate(
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
            response_model=QuestionResponse,
        )

        return PaginateQuestionResponse.model_validate(paginated_questions)
    except Exception as e:
        logger.error(e)
        handle_router_exception(e)


@router.post(
    "/",
    summary="Create Question",
    description="Create a new Question.",
    response_model=QuestionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_question(
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


@router.put(
    "/{question_id}",
    summary="Update Question",
    description="Update an existing Question.",
    response_model=QuestionResponse,
    status_code=status.HTTP_200_OK,
)
def update_question(
    question_id: int,
    request: QuestionCreate,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        service = QuestionService(db)
        payload = request.copy(update={"user_id": 1})
        question = service.update(question_id, payload)

        db.commit()
        return QuestionResponse.model_validate(question)
    except Exception as e:
        logger.error(e)
        db.rollback()
        handle_router_exception(e)


@router.get(
    "/{question_id}",
    summary="Get Question",
    description="Get a Question by ID.",
    response_model=QuestionResponse,
    status_code=status.HTTP_200_OK,
)
def get_question(
    question_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        service = QuestionService(db)
        question = service.get_by_id(question_id)

        return QuestionResponse.model_validate(question)
    except Exception as e:
        logger.error(e)
        handle_router_exception(e)
