from fastapi import Request, status, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError, IntegrityError


class ValidationException(Exception):
    def __init__(self, message: str):
        self.message = message


async def validation_exception_handler(request: Request, exc: ValidationException):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"success": False, "details": exc.message},
    )


async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    errors = {}
    for err in exc.errors():
        field = ".".join(str(loc) for loc in err["loc"][1:])
        message = err["msg"]
        errors[field] = message

        # Split the message by comma and take the second part (index 1)
        if "," in message:
            message = message.split(",")[1].strip()  # Strip spaces

        errors[field] = message

    return JSONResponse(
        status_code=422,
        content={"errors": errors},
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    if isinstance(exc, IntegrityError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "message": "Database integrity error.",
                "details": str(exc.orig),
            },
        )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "Database error occurred.",
            "details": str(exc),
        },
    )


async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "An unexpected error occurred.",
            "details": str(exc),
        },
    )
