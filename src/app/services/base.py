from typing import Type, TypeVar, Optional, List, Union, Callable, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import DeclarativeMeta
import math

T = TypeVar("T", bound=DeclarativeMeta)


class BaseService:
    def __init__(self, db: Session, model: Type[T]):
        """
        Base service for common CRUD operations.

        :param db: SQLAlchemy Session
        :param model: SQLAlchemy model class
        """
        self.db = db
        self.model = model

    def base_query(self, with_trashed: bool = False):
        """
        Create a base query excluding soft-deleted records by default.

        :param with_trashed: Include soft-deleted rows if True
        """
        query = self.db.query(self.model)
        if hasattr(self.model, "deleted_at") and not with_trashed:
            query = query.filter(self.model.deleted_at.is_(None))
        return query

    def find_one(
        self,
        *expressions,
        sort_by: str = "id",
        sort_order: str = "asc",
        with_trashed: bool = False,
        **filters,
    ) -> Optional[T]:
        """
        Find the first record matching filters and expressions.

        :param expressions: SQLAlchemy expressions (e.g., `Model.name == "test"`)
        :param filters: Keyword filters (e.g., `name="test"`)
        """
        query = self.base_query(with_trashed)
        if expressions:
            query = query.filter(*expressions)
        if filters:
            query = query.filter_by(**filters)

        # Sorting logic
        sort_column = getattr(self.model, sort_by, None)
        if sort_column is not None:
            if sort_order == "desc":
                sort_column = sort_column.desc()
            query = query.order_by(sort_column)

        return query.first()

    def find_all(
        self,
        *expressions,
        sort_by: str = "id",
        sort_order: str = "asc",
        with_trashed: bool = False,
        **filters,
    ) -> List[T]:
        """
        Find all records matching given expressions and filters.
        """
        query = self.base_query(with_trashed)
        if expressions:
            query = query.filter(*expressions)
        if filters:
            query = query.filter_by(**filters)

        # Sorting logic
        sort_column = getattr(self.model, sort_by, None)
        if sort_column is not None:
            if sort_order == "desc":
                sort_column = sort_column.desc()
            query = query.order_by(sort_column)

        return query.all()

    def get_by_id(
        self, record_id: Union[int, str], with_trashed: bool = False
    ) -> Optional[T]:
        """
        Get a record by its primary key.
        """
        return self.base_query(with_trashed).filter_by(id=record_id).first()

    def paginate(
        self,
        *expressions,
        page: int = 1,
        page_size: int = 10,
        sort_by: str = "id",
        sort_order: str = "asc",
        with_trashed: bool = False,
        response_model: Optional[Callable[[Any], Any]] = None,
        **filters,
    ) -> Dict[str, Any]:
        """
        Paginate records with optional response model validation.

        :param expressions: SQLAlchemy expressions to filter
        :param page: Current page number (1-based)
        :param page_size: Number of items per page
        :param sort_by: Column of items sort by
        :param sort_order: Direction of items sort order
        :param with_trashed: Whether to include soft-deleted records
        :param response_model: Pydantic model with `model_validate_list` classmethod
        :return: A dictionary with pagination metadata and serialized items
        """
        query = self.base_query(with_trashed)

        if expressions:
            query = query.filter(*expressions)
        if filters:
            query = query.filter_by(**filters)

        # Sorting logic
        sort_column = getattr(self.model, sort_by, None)
        if sort_column is not None:
            if sort_order == "desc":
                sort_column = sort_column.desc()
            query = query.order_by(sort_column)

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        result = {
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

        return result
