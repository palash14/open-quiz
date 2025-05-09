from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


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
