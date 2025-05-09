from sqlalchemy import create_engine, Table, MetaData, select, and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from src.app.core.config import settings
from typing import Optional, Any

# Create the SQLAlchemy engine using the database URI from settings
engine = create_engine(str(settings.DATABASE_URI))

# Create a configured "SessionLocal" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a base class for declarative class definitions
Base = declarative_base()


def get_db():
    """
    Dependency that provides a SQLAlchemy database session.

    Yields:
        Session: A SQLAlchemy session object.

    Ensures that the session is properly closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to get a specific field value from any table
def get_field_value(
    session: Session, table_name: str, field_name: str, value: Any, **filters
) -> Optional[dict]:
    """
    Generic function to fetch a row where `field_name` matches `value` in the given `table_name`, with optional additional filters.

    Args:
        session (Session): The database session.
        table_name (str): Name of the table to query.
        field_name (str): The field name to search by.
        value (Any): The value to search for (can be string, int, etc.).
        param filters: Additional optional filters (e.g., survey_id=1).

    Returns:
        Optional[dict]: Returns a dictionary of the row data if found, else None.
    """
    metadata = MetaData()
    table = Table(table_name, metadata, autoload_with=session.bind)

    # Create the initial query to match the main field
    query = select(table).where(table.c[field_name] == value)

    # Apply any additional filters dynamically
    if filters:
        filter_conditions = [table.c[key] == val for key, val in filters.items()]
        query = query.where(and_(*filter_conditions))

    result = session.execute(query).fetchone()

    return dict(result) if result else None
