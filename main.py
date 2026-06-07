from functools import lru_cache

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware
from tortoise.contrib.fastapi import register_tortoise

from routers import files_router, user_router
from config import Settings
from db import TORTOISE_ORM


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
    config=TORTOISE_ORM,
    generate_schemas=False,
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
settings = get_settings()

session_kwargs = {
    'secret_key': settings.secret_key,
}

if settings.cors_origin.startswith('http://localhost') or settings.cors_origin.startswith('http://127.0.0.1'):
    session_kwargs.update({
        'same_site': 'lax',
        'https_only': False,
    })
else:
    session_kwargs.update({
        'same_site': 'none',
        'https_only': True,
    })

app.add_middleware(SessionMiddleware, **session_kwargs)

app.include_router(files_router)
app.include_router(user_router)
