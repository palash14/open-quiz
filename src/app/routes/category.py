from typing import Annotated, List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from src.app.services.category_service import CategoryService

router = APIRouter(
    prefix="/categories",
    tags=["Category"],
    responses={404: {"description": "Not found"}},
)


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
    service = CategoryService(db)
    return service.create(request)
