# File: src/app/services/user_service.py
from sqlalchemy.orm import Session
from src.app.models.user import User
from src.app.schemas.user import UserCreate, UserUpdate
from src.app.utils.hashing import hash_password, verify_password
from fastapi import HTTPException, status
from typing import Optional
from random import randint
from datetime import timedelta, datetime

def random_with_n_digits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)

def find_one(db: Session, **kwargs) -> Optional[User]:
    """
    Find a single user based on the provided keyword arguments.

    This function queries the `User` model in the database using the given keyword 
    arguments as filter conditions. It returns the first user instance that matches 
    the criteria, or `None` if no user is found.

    :param db: The SQLAlchemy session object used to interact with the database.
    :param kwargs: Keyword arguments representing the filter conditions for querying 
                   the user. For example, `email="user@example.com"`.

    :return: The `User` instance that matches the filter conditions, or `None` 
             if no matching user is found.
    :rtype: User
    """
    return db.query(User).filter_by(**kwargs).first()


def create(db: Session, user_create: UserCreate) -> User:
    """
    Create a new user in the database.

    This function creates a new `User` instance using the data provided in the 
    `UserCreate` schema. The user's password is hashed before storing it. The 
    new user is added to the database session and the changes are flushed to ensure 
    that the user's ID is available.

    :param db: The SQLAlchemy session object used to interact with the database. 
    :param user_create: A `UserCreate` schema instance containing the data required 
                        to create a new user. It includes:
                        - `name`: The name of the user.
                        - `email`: The user's email address.
                        - `phone_no`: The user's phone number.
                        - `dial_code`: The dial code for the user's phone number.
                        - `password`: The user's plain text password.

    :return: The newly created `User` instance with a hashed password.
    :rtype: User
    """
    # Hash the password
    hashed_password = hash_password(user_create.password)

    email_token_expired_at = datetime.today() + timedelta(1)
    otp_expired_at = datetime.today() + timedelta(minutes=10)
    # Create a new user instance
    new_user = User(
        email=user_create.email,
        name=user_create.name,
        phone_no=None,
        dial_code=None,
        password=hashed_password,
        email_verify_token= random_with_n_digits(5),
        email_verify_expired_at = email_token_expired_at,
        phone_otp=random_with_n_digits(5),
        phone_otp_expired_at =otp_expired_at
    )

    # Add the new user to the session
    db.add(new_user)    
    db.flush()  # Flush to ensure new_user.id is available    

    return new_user

def update_user(db: Session, user_id: int, user_update: UserUpdate) -> User:
    """
    Update an existing user in the database.

    This function updates specific fields of an existing `User` instance. It uses
    the provided `user_id` to identify the user, and the `UserUpdate` schema to
    determine which fields need to be updated. If the `password` is updated, it
    will be hashed before saving to the database.

    :param db: The SQLAlchemy session object used to interact with the database.
    :param user_id: The ID of the user to be updated.
    :param user_update: A `UserUpdate` schema instance containing the fields
                        to be updated.

    :return: The updated `User` instance.
    :rtype: User
    """
    # Find the user by ID
    user = find_one(db, id=user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Update the fields if they are provided in the user_update payload
        
    if user_update.name is not None:
        user.name = user_update.name

    if user_update.email is not None:
        user.email = user_update.email

    if user_update.phone_no is not None:
        user.phone_no = user_update.phone_no

    if user_update.dial_code is not None:
        user.dial_code = user_update.dial_code 
        
    # Update the user_name if provided
    if user_update.user_name is not None:
        user.user_name = user_update.user_name     
        
    # Commit the changes to the database
    db.commit()
    db.refresh(user)  # Refresh to ensure the instance has updated values

    return user


def change_password(db: Session, user: User, old_password: str, new_password: str) -> User:
    """
    Change the password of an existing user.

    :param db: The SQLAlchemy session.
    :param user: The user instance.
    :param old_password: The current password of the user.
    :param new_password: The new password to be set.
    :return: The updated user instance.
    """
    # Verify the current password
    if not verify_password(old_password, user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect."
        )

    # Hash the new password and update it
    user.password = hash_password(new_password)
    db.commit()
    db.refresh(user)

    return user
