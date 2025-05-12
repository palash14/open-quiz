from typing import Annotated, List
from fastapi import APIRouter, Depends, status, HTTPException, status
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
        category = service.create(request)

        db.commit()
        return CategoryResponse.model_validate(category)
    except Exception as e:
        logger.error(e)
        db.rollback()
        handle_router_exception(e)


@router.get(
    "/",
    summary="Get all Categories",
    description="Retrieve all Categories.",
    response_model=List[CategoryResponse],
    status_code=status.HTTP_200_OK,
)
def get_category(
    db: Annotated[Session, Depends(get_db)],
):
    try:
        service = CategoryService(db)
        categories = service.find_all()

        return [CategoryResponse.model_validate(category) for category in categories]
    except Exception as e:
        logger.error(e)
        handle_router_exception(e)


@router.get(
    "/{category_id}",
    summary="Get Category by ID",
    description="Retrieve a Category by its ID.",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
)
def get_category_by_id(
    category_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        service = CategoryService(db)
        category = service.get_by_id(record_id=category_id)

        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found.",
            )

        return CategoryResponse.model_validate(category)
    except Exception as e:
        logger.error(e)
        handle_router_exception(e)


@router.put(
    "/{category_id}",
    summary="Update Category",
    description="Update an existing Category.",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
)
def update_category(
    category_id: int,
    request: CategoryUpdate,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        service = CategoryService(db)
        category = service.update(category_id, request)

        db.commit()
        return CategoryResponse.model_validate(category)
    except Exception as e:
        logger.error(e)
        db.rollback()
        handle_router_exception(e)


@router.delete(
    "/{category_id}",
    summary="Delete Category",
    description="Delete an existing Category.",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_category(
    category_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    try:
        service = CategoryService(db)
        service.delete(category_id)
        db.commit()

    except Exception as e:
        logger.error(e)
        db.rollback()
        handle_router_exception(e)
