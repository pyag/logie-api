from functools import lru_cache

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware
from tortoise.contrib.fastapi import register_tortoise

from files import router as files_router
from routers import user_router
from config import Settings


def format_api_response(status_code: int, message: str, success: bool = True, data: dict | None = None):
    payload = {
        "status_code": status_code,
        "success": success,
        "message": message,
    }
    if data is not None:
        payload["data"] = data
    return JSONResponse(status_code=status_code, content=payload)


@lru_cache
def get_settings():
    return Settings()

origins = [get_settings().cors_origin]

app = FastAPI()

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return format_api_response(
        status_code=exc.status_code,
        message=str(exc.detail),
        success=False,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return format_api_response(
        status_code=422,
        message="Validation error",
        success=False,
        data={"errors": exc.errors()},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return format_api_response(
        status_code=500,
        message="An unexpected error occurred.",
        success=False,
    )

# Register Tortoise ORM with FastAPI
register_tortoise(
    app,
    db_url=get_settings().db_url,
    modules={'models': ['dbmodels']},
    generate_schemas=True,
    add_exception_handlers=True,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,  # Allow cookies for cross-origin requests
    allow_methods=["*"],
    allow_headers=["*"],
)

# Starlette session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=get_settings().secret_key
)

app.include_router(files_router)
app.include_router(user_router)
