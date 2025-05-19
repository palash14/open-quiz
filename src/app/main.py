# File: src/app/main.py
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.middleware.sessions import SessionMiddleware
from src.app.routes import quiz, category, auth, auth_github, question
from src.app.core.swagger import custom_openapi
from src.app.utils.exceptions import (
    ValidationException,
    request_validation_exception_handler,
    validation_exception_handler,
    sqlalchemy_exception_handler,
    generic_exception_handler
)
from src.app.core.config import settings
from sqlalchemy.exc import SQLAlchemyError

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESC,
    version=settings.VERSION,
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY  # Use a secure, random key
)

# Register the custom exception handler
app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
app.add_exception_handler(ValidationException, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)

# Set custom OpenAPI generator
app.openapi = lambda: custom_openapi(app)

app.include_router(quiz.router)
app.include_router(auth.router)
app.include_router(auth_github.router)
app.include_router(category.router)
app.include_router(question.router)
