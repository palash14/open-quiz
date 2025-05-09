from typing import Annotated, List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from src.app.services.category_service import CategoryService
from src.app.core.logger import create_logger
from src.app.utils.exceptions import handle_router_exception

router = APIRouter(
    prefix="/categories",
    tags=["Category"],
    responses={404: {"description": "Not found"}},
)

logger = create_logger("category", "routers_category.log")


@router.post(
    "/",
    summary="Create Category",
    description="Create a new Category.",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_category(
    request: CategoryCreate,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        service = CategoryService(db)
        service.create(request)

        # Commit the transaction
        db.commit()
    except Exception as e:
        logger.error(e)
        # Rollback any changes made in the current session
        db.rollback()
        handle_router_exception(e)
