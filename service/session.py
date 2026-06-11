import logging
from datetime import datetime
from fastapi import HTTPException, Request, status
from service.auth import decode_access_token

logger = logging.getLogger("uvicorn.error")

def create_session(request: Request, locker, root_id: str) -> None:
    """Store user information in the session after successful signup/login."""
    request.session.update({
        'user_id': str(locker.uid),
        'locker_name': locker.name,
        'email': locker.email,
        'root_id': root_id,
        'authenticated': True,
        'session_created': datetime.now().isoformat(),
    })


def _get_session_user(request: Request) -> dict | None:
    """Retrieve current user info from the session."""
    if request.session.get('authenticated'):
        return {
            'user_id': request.session.get('user_id'),
            'locker_name': request.session.get('locker_name'),
            'email': request.session.get('email'),
            'root_id': request.session.get('root_id'),
            'session_created': request.session.get('session_created'),
        }
    return None


def get_current_user(request: Request) -> dict:
    """FastAPI auth dependency: prefer Bearer token, fall back to session."""
    auth_header = request.headers.get('authorization')
    if auth_header and auth_header.lower().startswith('bearer '):
        token = auth_header.split(' ', 1)[1].strip()
        try:
            payload = decode_access_token(token)
            return {
                'user_id': payload.get('user_id'),
                'locker_name': payload.get('locker_name'),
                'email': payload.get('email'),
                'root_id': payload.get('root_id'),
                'session_created': payload.get('session_created'),
            }
        except Exception:
            logger.warning("Invalid Bearer token provided")
            return None

    user = _get_session_user(request)
    if not user:
        return None

    return user


def clear_session(request: Request) -> None:
    """Clear the user session (logout)."""
    request.session.clear()
