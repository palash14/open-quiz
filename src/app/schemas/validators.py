# File: src/app/schemas/validators.py
import re 

class CommonValidators:
    def validate_email_format(cls, v: str) -> str:
        regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(regex, v):
            raise ValueError("Invalid email format")
        return v


    def validate_non_empty_token(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError( "token cannot be empty" )
        return v

   
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long" )
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v
