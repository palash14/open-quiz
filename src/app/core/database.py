from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.app.core.config import settings

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
