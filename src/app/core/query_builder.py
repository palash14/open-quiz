from typing import Type, TypeVar, Optional, List, Generic, Any
from sqlalchemy.orm import Session, Query, joinedload
from sqlalchemy.ext.declarative import DeclarativeMeta
from sqlalchemy import asc, desc
import math

T = TypeVar("T", bound=DeclarativeMeta)


class QueryBuilder(Generic[T]):
    def __init__(self, db: Session, model: Type[T]):
        self.db = db
        self.model = model
        self.query: Query = db.query(model)
        self.__with_trashed = False
        self.__apply_soft_delete_filter()

    def __apply_soft_delete_filter(self):
        if not self.__with_trashed and hasattr(self.model, "deleted_at"):
            self.query = self.query.filter(getattr(self.model, "deleted_at").is_(None))

    def with_trashed(self) -> "QueryBuilder":
        self.__with_trashed = True
        self.query = self.db.query(self.model)
        return self

    def where(self, *expressions, **filters) -> "QueryBuilder":
        if expressions:
            self.query = self.query.filter(*expressions)
        if filters:
            self.query = self.query.filter_by(**filters)
        return self

    def where_like(self, field: str, value: str) -> "QueryBuilder":
        if hasattr(self.model, field):
            self.query = self.query.filter(
                getattr(self.model, field).ilike(f"%{value}%")
            )
        return self

    def where_relation(
        self, relation: Any, related_field: str, value: Any
    ) -> "QueryBuilder":
        self.query = self.query.join(relation).filter(
            getattr(relation, related_field) == value
        )
        return self

    def where_relation_like(
        self, relation: Any, related_field: str, value: str
    ) -> "QueryBuilder":
        self.query = self.query.join(relation).filter(
            getattr(relation, related_field).ilike(f"%{value}%")
        )
        return self

    def with_relationships(self, *relations: str) -> "QueryBuilder":
        for rel in relations:
            self.query = self.query.options(joinedload(rel))
        return self

    def order_by(self, field: str, direction: str = "asc") -> "QueryBuilder":
        sort_column = getattr(self.model, field, None)
        if not sort_column:
            raise ValueError(f"Invalid sort field: {field}")
        self.query = self.query.order_by(
            asc(sort_column) if direction == "asc" else desc(sort_column)
        )
        return self

    def paginate(
        self, page: int = 1, page_size: int = 10, response_model: Optional[Any] = None
    ) -> dict:
        total = self.query.count()
        items = self.query.offset((page - 1) * page_size).limit(page_size).all()
        return {
            "items": (
                [response_model.from_orm(item) for item in items]
                if response_model
                else items
            ),
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size),
        }

    def all(self) -> List[T]:
        return self.query.all()

    def first(self) -> Optional[T]:
        return self.query.first()
