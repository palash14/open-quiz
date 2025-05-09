import logging
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from src.app.models.user import User, UserStatusEnum, UserTypeEnum

# Initialize CryptContext with bcrypt hashing scheme
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """
    Hashes a plain text password using bcrypt.

    Args:
        password (str): The plain text password to be hashed.

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)


def upsert_users(db: Session) -> None:
    """
    Performs an upsert (insert or do nothing) operation to create multiple users
    in the database based on the email. If the user already exists, do nothing.

    Args:
        db (Session): The database session used for adding the user.
    """
    try:
        # List of user data to be upserted
        users_data = [
            {
                "name": "Palash Pramanick",
                "email": "palash14@gmail.com",
                "phone_no": "1234567890",
                "dial_code": "+91",
                "password": hash_password("password123"),
                "status": UserStatusEnum.active,
                "user_type": UserTypeEnum.authorized,
            },
            {
                "name": "Diptendu Barman",
                "email": "diptendubarman40@gmail.com",
                "phone_no": "1234567899",
                "dial_code": "+91",
                "password": hash_password("password123"),
                "status": UserStatusEnum.active,
                "user_type": UserTypeEnum.authorized,
            },
            # Add more users as needed
        ]

        # Prepare the insert statement for multiple rows
        stmt = insert(User).values(users_data)
        stmt = stmt.on_conflict_do_nothing(
            index_elements=["email"]
        )  # Conflict resolution on email

        # Execute the statement to insert users
        db.execute(stmt)
        db.commit()
        logger.info(f"Successfully upserted {len(users_data)} users.")
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
        upsert_users(db)
        logger.info("Seeding process completed successfully.")
    except Exception as e:
        logger.error(f"Seeding process failed: {e}")
