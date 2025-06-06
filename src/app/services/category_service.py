# File: src/app/services/category_service.py
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.models.category import Category
from src.app.schemas.category import CategoryCreate, CategoryUpdate
from src.app.services.base_service import BaseService
from src.app.utils.exceptions import ValidationException, RecordNotFoundException


class CategoryService(BaseService):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Category)

    async def create(self, payload: CategoryCreate) -> Category:
        existing = await self.find_one(name=payload.name)
        if existing:
            raise ValidationException("Category name already exists.")

        category = Category(
            name=payload.name,
            description=payload.description,
        )
        self.db.add(category)
        await self.db.commit()
        await self.db.flush()
        await self.db.refresh(category)
        return category

    async def update(self, category_id: int, payload: CategoryUpdate) -> Category:
        category = await self.find_one(id=category_id)
        if not category:
            raise RecordNotFoundException("Category not found.")

        if payload.name and payload.name != category.name:
            existing = await self.find_one(Category.id != category_id, name=payload.name)
            if existing:
                raise ValidationException("Category name already exists.")

        for key, value in payload.dict(exclude_unset=True).items():
            setattr(category, key, value)

        await self.db.flush()
        await self.db.refresh(category)
        return category

    async def delete(self, category_id: int) -> None:
        """
        Soft delete a category by setting deleted_at timestamp.
        """
        category = await self.find_by_id(record_id=category_id)

        # If category not found or already deleted, raise an exception
        if not category:
            raise RecordNotFoundException("Category not found.")

        # Soft delete the category by setting the deleted_at timestamp
        category.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
        return None

