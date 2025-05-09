from fastapi import Request, status, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError, IntegrityError


async def custom_validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    errors = {}
    for err in exc.errors():
        field = err["loc"][-1]
        message = err["msg"]
        errors[field] = message
    return JSONResponse(
        status_code=422,
        content={"errors": errors},
    )

def handle_router_exception(e: Exception) -> None:
    """
    Centralized exception handler to rollback the database session and raise an HTTPException.

    :param e: The caught exception.
    :raises HTTPException: With appropriate status code and error details.
    """
    # Propagate already raised HTTPException without modification
    if isinstance(e, HTTPException):
        raise e

    # Handle database-specific exceptions
    if isinstance(e, IntegrityError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Integrity error: {str(e.orig)}",
            headers={
                "X-Error-Detail": str(e)
            },  # Additional error details for debugging purposes
        )
    elif isinstance(e, SQLAlchemyError):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="A database error occurred. Please try again later.",
            headers={
                "X-Error-Detail": str(e)
            },  # Additional error details for debugging purposes
        )

    # Handle all other types of exceptions
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="An unexpected error occurred. Please try again later.",
        headers={
            "X-Error-Detail": str(e)
        },  # Additional error details for debugging purposes
    )
