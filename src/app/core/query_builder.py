# File: src/app/core/query_builder.py
from typing import Sequence, Type, TypeVar, Optional, List, Generic, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select, asc, desc
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy import select, func
import math

T = TypeVar("T", bound=DeclarativeMeta)


class QueryBuilder(Generic[T]):
    def __init__(self, db: AsyncSession, model: Type[T]):
        self.db = db
        self.model = model
        self.query: Select = select(model)
        self.__with_trashed = False
        self.__apply_soft_delete_filter()

    async def __apply_soft_delete_filter(self):
        if not self.__with_trashed and hasattr(self.model, "deleted_at"):
            self.query = self.query.filter(getattr(self.model, "deleted_at").is_(None))

    async def with_trashed(self) -> "QueryBuilder[T]":
        self.__with_trashed = True
        self.query = select(self.model)
        return self

    async def where(self, *expressions, **filters) -> "QueryBuilder[T]":
        if expressions:
            self.query = self.query.filter(*expressions)
        if filters:
            self.query = self.query.filter_by(**filters)
        return self

    async def where_like(self, field: str, value: str) -> "QueryBuilder[T]":
        if hasattr(self.model, field):
            self.query = self.query.filter(
                getattr(self.model, field).ilike(f"%{value}%")
            )

        return self

    async def where_relation(
        self, relation: Any, related_field: str, value: Any
    ) -> "QueryBuilder":
        self.query = self.query.join(relation).filter(
            getattr(relation, related_field) == value
        )
        return self

    async def where_relation_like(
        self, relation: Any, related_field: str, value: str
    ) -> "QueryBuilder":
        self.query = self.query.join(relation).filter(
            getattr(relation, related_field).ilike(f"%{value}%")
        )
        return self

    async def with_relationships(self, *relations: str) -> "QueryBuilder[T]":
        for rel in relations:
            relationship_attr = getattr(self.model, rel, None)
            if relationship_attr is None:
                raise ValueError(f"Model {self.model.__name__} has no relationship '{rel}'")
            self.query = self.query.options(joinedload(relationship_attr))
        return self

    async def order_by(self, field: str, direction: str = "asc") -> "QueryBuilder[T]":
        sort_column = getattr(self.model, field, None)
        if not sort_column:
            raise ValueError(f"Invalid sort field: {field}")
        self.query = self.query.order_by(
            asc(sort_column) if direction == "asc" else desc(sort_column)
        )
        return self

    async def paginate(
        self, page: int = 1, page_size: int = 10, response_model: Optional[Any] = None
    ) -> dict:
        # Get total count
        count_query = self.query.with_only_columns(func.count()).order_by(None)
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Get paginated items
        items_query = self.query.offset((page - 1) * page_size).limit(page_size)
        items_result = await self.db.execute(items_query)
        items: Sequence[T] = items_result.scalars().all()

        return {
            "items": (
                [response_model.from_orm(item) for item in items]
                if response_model
                else list(items)
            ),
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size),
        }

    async def all(self) -> List[T]:
        result = await self.db.execute(self.query)
        return list(result.scalars().all())

    async def first(self) -> Optional[T]:
        result = await self.db.execute(self.query)
        return result.scalars().first()

    async def count(self) -> int:
        count_query = self.query.with_only_columns(func.count()).order_by(None)
        result = await self.db.execute(count_query)
        return result.scalar_one()
