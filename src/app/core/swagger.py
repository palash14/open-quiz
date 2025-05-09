from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI
from src.app.core.config import settings


def custom_openapi(app: FastAPI):
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESC,
        version=settings.VERSION,
        routes=app.routes,
    )

    openapi_schema["components"]["schemas"]["HTTPValidationError"] = {
        "title": "CustomValidationError",
        "type": "object",
        "properties": {
            "errors": {
                "type": "object",
                "additionalProperties": {"type": "string"},
                "example": {
                    "name": "name is required",
                    "email": "invalid email format",
                },
            }
        },
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema
