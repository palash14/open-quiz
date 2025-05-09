# database/run_seeder.py
from src.app.core.database import get_db
from sqlalchemy.orm import Session
from database.seeders import user_seeder


def run_seeder():
    """
    Run all seeders to populate the database.
    """
    # Get a new database session from the generator
    db_gen = get_db()
    db: Session = next(db_gen)  # Extract session object from generator

    try:
        # Begin transaction
        with db.begin():
            user_seeder.run(db)

        # Commit the transaction
        db.commit()

    except Exception as e:
        print(f"Error while seeding: {e}")
        db.rollback()

    finally:
        # Close the database session
        db.close()
        next(db_gen, None)  # Ensure the generator is finalized


if __name__ == "__main__":
    run_seeder()
