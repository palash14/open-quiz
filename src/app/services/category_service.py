from typing import List, Optional
from sqlalchemy.orm import Session
from src.app.models.category import Category
from src.app.schemas.category import CategoryCreate, CategoryUpdate
from datetime import datetime, timezone


class CategoryService:
    def __init__(self, db: Session):
        self.db = db

    def find_one(self, **filters) -> Optional[Category]:
        """
        Find a single category by given filters.
        """
        return (
            self.db.query(Category)
            .filter_by(**filters)
            .filter(Category.deleted_at.is_(None))
            .first()
        )

    def find_all(self, **filters) -> List[Category]:
        """
        Find all categories matching given filters.
        """
        return (
            self.db.query(Category)
            .filter_by(**filters)
            .filter(Category.deleted_at.is_(None))
            .all()
        )

    def create(self, payload: CategoryCreate) -> Category:
        """
        Create a new category.
        """
        category = Category(
            name=payload.name,
            description=payload.description,
        )
        self.db.add(category)
        self.db.flush()
        return category

    def update(self, category_id: int, payload: CategoryUpdate) -> Optional[Category]:
        """
        Update an existing category.
        """
        category = self.db.query(Category).filter_by(id=category_id).first()
        if not category:
            return None

        for key, value in payload.dict(exclude_unset=True).items():
            setattr(category, key, value)

        self.db.flush()
        return category

    def delete(self, category_id: int) -> bool:
        """
        Soft delete a category by setting deleted_at timestamp.
        """
        category = self.db.query(Category).filter_by(id=category_id).first()
        if not category or category.deleted_at is not None:
            return False

        category.deleted_at = datetime.now(timezone.utc)
        self.db.flush()
        return True
