from typing import Type, TypeVar, Optional, List, Union
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import DeclarativeMeta
from src.app.core.query_builder import QueryBuilder

T = TypeVar("T", bound=DeclarativeMeta)


class BaseService:
    def __init__(self, db: Session, model: Type[T]):
        self.db = db
        self.model = model

    def builder(self, with_trashed: bool = False) -> QueryBuilder:
        builder = QueryBuilder(self.db, self.model)
        return builder.with_trashed() if with_trashed else builder

    def find_one(
        self,
        *expressions,
        sort_by: str = "id",
        sort_order: str = "asc",
        with_trashed: bool = False,
        **filters,
    ) -> Optional[T]:
        return (
            self.builder(with_trashed)
            .where(*expressions, **filters)
            .order_by(sort_by, sort_order)
            .first()
        )

    def find_all(
        self,
        *expressions,
        sort_by: str = "id",
        sort_order: str = "asc",
        with_trashed: bool = False,
        **filters,
    ) -> List[T]:
        return (
            self.builder(with_trashed)
            .where(*expressions, **filters)
            .order_by(sort_by, sort_order)
            .all()
        )

    def find_by_id(
        self, record_id: Union[int, str], with_trashed: bool = False
    ) -> Optional[T]:
        return self.builder(with_trashed).where(id=record_id).first()
