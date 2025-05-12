# File: src/app/services/user_service.py
from sqlalchemy.orm import Session
from src.app.models.user import User
from src.app.schemas.user import UserCreate, UserUpdate
from src.app.utils.hashing import hash_password, verify_password
from fastapi import HTTPException, status
from typing import Optional
from random import randint
from datetime import timedelta, datetime
from src.app.services.base import BaseService


class UserService(BaseService):
    def __init__(self, db: Session):
        super().__init__(db, User)

    def generate_otp(self, n: int = 5):
        range_start = 10 ** (n - 1)
        range_end = (10**n) - 1
        return randint(range_start, range_end)

    def create(self, payload: UserCreate) -> User:
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
        hashed_password = hash_password(payload.password)

        email_token_expired_at = datetime.today() + timedelta(1)
        # Create a new user instance
        new_user = User(
            email=payload.email,
            name=payload.name,
            phone_no=None,
            dial_code=None,
            password=hashed_password,
            email_verify_token=self.generate_otp(5),
            email_verify_expired_at=email_token_expired_at
        )

        # Add the new user to the session
        self.db.add(new_user)
        self.db.flush()  # Flush to ensure new_user.id is available

        return new_user

    def update_user(self, user_id: int, payload: UserUpdate) -> User:
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
        user = self.find_one(id=user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Update the fields if they are provided in the user_update payload

        for key, value in payload.dict(exclude_unset=True).items():
            setattr(user, key, value)

        # Commit the changes to the database
        self.db.commit()
        self.db.refresh(user)  # Refresh to ensure the instance has updated values

        return user

    def change_password(self, user: User, old_password: str, new_password: str) -> User:
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
                detail="Current password is incorrect.",
            )

        # Hash the new password and update it
        user.password = hash_password(new_password)
        self.db.commit()
        self.db.refresh(user)

        return user
