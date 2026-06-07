from datetime import datetime, timedelta
from typing import Any, Dict

import jwt

from config import get_settings

settings = get_settings()
SECRET = settings.jwt_secret
ALGORITHM = "HS256"


def create_access_token(data: Dict[str, Any], expires_minutes: int | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=(expires_minutes or settings.jwt_exp_minutes))
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET, algorithm=ALGORITHM)
    return token


def decode_access_token(token: str) -> Dict[str, Any]:
    payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM])
    return payload
