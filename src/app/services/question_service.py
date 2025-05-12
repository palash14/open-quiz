from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from src.app.models.question import Question
from src.app.schemas.question import QuestionCreate, QuestionUpdate
from src.app.services.base import BaseService


class QuestionService(BaseService):
    def __init__(self, db: Session):
        super().__init__(db, Question)

    def create(self, payload: QuestionCreate) -> Question:
        # existing = self.find_one(name=payload.name)
        # if existing:
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST,
        #         detail="Category name already exists.",
        #     )

        # category = Question(
        #     name=payload.name,
        #     description=payload.description,
        # )
        # self.db.add(category)
        # self.db.flush()
        # return category
        pass

    def update(self, category_id: int, payload: QuestionUpdate) -> Question:
        # category = self.find_one(id=category_id)
        # if not category:
        #     raise HTTPException(
        #         status_code=status.HTTP_404_NOT_FOUND,
        #         detail="Category not found.",
        #     )

        # if payload.name and payload.name != category.name:
        #     existing = self.find_one(Question.id != category_id, name=payload.name)
        #     if existing:
        #         raise HTTPException(
        #             status_code=status.HTTP_400_BAD_REQUEST,
        #             detail="Category name already exists.",
        #         )

        # for key, value in payload.dict(exclude_unset=True).items():
        #     setattr(category, key, value)

        # self.db.flush()
        # return category
        pass

    def delete(self, category_id: int) -> None:
        """
        Soft delete a category by setting deleted_at timestamp.
        """
        # category = self.get_by_id(record_id=category_id)

        # # If category not found or already deleted, raise an exception
        # if not category:
        #     raise HTTPException(
        #         status_code=status.HTTP_404_NOT_FOUND,
        #         detail="Category not found.",
        #     )

        # # Soft delete the category by setting the deleted_at timestamp
        # category.deleted_at = datetime.now(timezone.utc)
        # self.db.flush()
        pass
