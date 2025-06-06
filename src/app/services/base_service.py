# File: src/app/services/base_service.py
from typing import Any, Type, TypeVar, Optional, List, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import DeclarativeMeta
from src.app.core.query_builder import QueryBuilder

T = TypeVar("T", bound=DeclarativeMeta)


class BaseService:
    def __init__(self, db: AsyncSession, model: Type[T]):
        self.db = db
        self.model = model

    async def builder(self, with_trashed: bool = False) -> QueryBuilder:
        builder = QueryBuilder(self.db, self.model)
        return await builder.with_trashed() if with_trashed else builder

    async def find_one(
        self,
        *expressions: Any,
        sort_by: str = "id",
        sort_order: str = "asc",
        with_trashed: bool = False,
        **filters,
    ) -> Optional[T]:
        builder = await self.builder(with_trashed)
        # Apply conditions - need to await each builder operation
        builder = await builder.where(*expressions, **filters)
        builder = await builder.order_by(sort_by, sort_order)

        return await builder.first()

    async def find_all(
        self,
        *expressions,
        sort_by: str = "id",
        sort_order: str = "asc",
        with_trashed: bool = False,
        **filters,
    ) -> List[T]:
        builder = await self.builder(with_trashed)
        # Apply conditions - need to await each builder operation
        builder = await builder.where(*expressions, **filters)
        builder = await builder.order_by(sort_by, sort_order)
        return await builder.all()

    async def find_by_id(
        self, record_id: Union[int, str], with_trashed: bool = False
    ) -> Optional[T]:
        try:
            pk_attr = getattr(self.model, "id")
        except AttributeError:
            raise ValueError(f"Model {self.model.__name__} has no 'id' primary key")

        builder = await self.builder(with_trashed)
        builder = await builder.where(pk_attr == record_id)
        return await builder.first()
    
