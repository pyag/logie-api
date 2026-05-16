from functools import lru_cache

from config import Settings

@lru_cache
def get_settings():
    return Settings()

TORTOISE_ORM = {
    "connections": {
        "default": get_settings().db_url,
    },
    "apps": {
        "models": {
            "models": ["dbmodels"],
            "default_connection": "default",
            "migrations": "migrations",
        },
    },
}
