# File: src/app/utils/hashing.py
from passlib.context import CryptContext

# Initialize CryptContext with sha256_crypt hashing scheme
pwd_context = CryptContext(schemes=["sha256_crypt"])


def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt.

    :param password: The plain text password to be hashed.
    :return: The hashed password.
    """
    try:
        if not password:
            raise ValueError("Password cannot be empty")
        # Hash the password securely using sha256_crypt
        return pwd_context.hash(password)
    except Exception as e:
        # Handle unexpected errors securely
        raise RuntimeError(f"Password hashing failed: {e}")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.

    :param plain_password: The plain text password to verify.
    :param hashed_password: The hashed password to compare against.
    :return: True if the plain password matches the hashed password, False otherwise.
    """

    try:
        # Safely verify the password and return the result
        return pwd_context.verify(plain_password, hashed_password)
    except ValueError:
        # Handle case where the hashed password is invalid or corrupted
        return False
    except Exception:
        # Handle any other unexpected exceptions securely
        return False