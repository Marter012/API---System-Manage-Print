from fastapi import Request,HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

async def validation_exception_handler(
    request : Request,
    exc : RequestValidationError
):
    return JSONResponse(
        status_code = 422,
        content={
            "message": "Validation error",
            "errors": exc.errors()
        }
    )
    
async def http_exception_handler(
    request: Request,
    exc: HTTPException
):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.detail,
            "status_code": exc.status_code
        }
    )
    
async def general_exception_handler(
    request: Request,
    exc: Exception
):
    return JSONResponse(
        status_code=500,
        content={
            "message": "Internal server error",
            "status_code": 500
        }
    )