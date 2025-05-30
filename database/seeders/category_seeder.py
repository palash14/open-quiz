import logging
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from src.app.models.category import Category
from src.app.schemas.category import CategoryCreate

import requests

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def upsert_categories(db: Session) -> None:
    """
    Performs an upsert (insert or do nothing) operation to create multiple categories
    in the database based on the email. If the user already exists, do nothing.

    Args:
        db (Session): The database session used for adding the user.
    """
    try:
        category_data = [
            {"name": "General Knowledge"},
            {"name": "Entertainment: Books"},
            {"name": "Entertainment: Film"},
            {"name": "Entertainment: Music"},
            {"name": "Entertainment: Musicals &amp; Theatres"},
            {"name": "Entertainment: Television"},
            {"name": "Entertainment: Video Games"},
            {"name": "Entertainment: Board Games"},
            {"name": "Science &amp; Nature"},
            {"name": "Science: Computers"},
            {"name": "Science: Mathematics"},
            {"name": "Mythology"},
            {"name": "Sports"},
            {"name": "Geography"},
            {"name": "Entertainment: Comics"},
            {"name": "Science: Gadgets"},
            {"name": "Entertainment: Japanese Anime &amp; Manga"},
            {"name": "History"},
            {"name": "Politics"},
            {"name": "Art"},
            {"name": "Celebrities"},
            {"name": "Animals"},
            {"name": "Vehicles"},
            {"name": "Entertainment: Cartoon &amp; Animations"},
        ]
        # Prepare the insert statement for multiple rows
        stmt = insert(Category).values(category_data)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["name"]
        )  # Conflict resolution on email

        # Execute the statement to insert users
        db.execute(stmt)
        db.commit()
        logger.info(f"Successfully upsetter {len(category_data)} categories.")
    except Exception as e:
        logger.error(f"Error during upsert: {e}")
        db.rollback()


def run(db: Session):
    """
    Seeds the database with users if one does not already exist.

    Args:
        db (Session): The database session used for querying and adding records.
    """
    try:
        logger.info("Running seeder...")
        upsert_categories(db)
        logger.info("Seeding process completed successfully.")
    except Exception as e:
        logger.error(f"Seeding process failed: {e}")
        raise e

