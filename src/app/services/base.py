from typing import Type, TypeVar, Optional, List, Union
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import DeclarativeMeta

T = TypeVar("T", bound=DeclarativeMeta)


class BaseService:
    def __init__(self, db: Session, model: Type[T]):
        """
        Base service for common CRUD operations.
        """
        self.db = db
        self.model = model

    def base_query(self, with_trashed: bool = False):
        """
        Returns a query object, filtering out soft-deleted records unless with_trashed=True.
        """
        query = self.db.query(self.model)
        if hasattr(self.model, "deleted_at") and not with_trashed:
            query = query.filter(self.model.deleted_at.is_(None))
        return query

    def find_one(
        self, *expressions, with_trashed: bool = False, **filters
    ) -> Optional[T]:
        """
        Find the first record matching given expressions and filters.
        """
        query = self.base_query(with_trashed=with_trashed)
        if expressions:
            query = query.filter(*expressions)
        if filters:
            query = query.filter_by(**filters)
        return query.first()

    def find_all(self, *expressions, with_trashed: bool = False, **filters) -> List[T]:
        """
        Find all records matching given expressions and filters.
        """
        query = self.base_query(with_trashed=with_trashed)
        if expressions:
            query = query.filter(*expressions)
        if filters:
            query = query.filter_by(**filters)
        return query.all()

    def get_by_id(
        self, record_id: Union[int, str], with_trashed: bool = False
    ) -> Optional[T]:
        """
        Get a record by its primary key.
        """
        return (
            self.base_query(with_trashed=with_trashed).filter_by(id=record_id).first()
        )
