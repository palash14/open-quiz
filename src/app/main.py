# src/app/main.py
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from src.app.routes import quiz, category, question
from src.app.core.swagger import custom_openapi
from src.app.utils.exceptions import custom_validation_exception_handler
from src.app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESC,
    version=settings.VERSION,
)

# Register the custom exception handler
app.add_exception_handler(RequestValidationError, custom_validation_exception_handler)

# Set custom OpenAPI generator
app.openapi = lambda: custom_openapi(app)

app.include_router(quiz.router)
# app.include_router(auth.router)
app.include_router(category.router)
app.include_router(question.router)
