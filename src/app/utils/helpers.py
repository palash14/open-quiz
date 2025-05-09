import random


def generate_otp() -> str:
    """
    Generates a 6-digit numeric code as a string.
    Always returns exactly six digits (e.g., '000123', '984561').

    Returns:
        str: A 6-digit string.
    """
    return f"{random.randint(0, 999999):06d}"
