from functools import lru_cache

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from tortoise.contrib.fastapi import register_tortoise, Tortoise

from files import router as files_router
from config import Settings

@lru_cache
def get_settings():
    return Settings()

origins = [get_settings().cors_origin]

app = FastAPI()

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
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(files_router)
