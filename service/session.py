from datetime import datetime
from fastapi import Request

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

def get_current_user(request: Request) -> dict | None:
    """Retrieve current user info from session."""
    if request.session.get('authenticated'):
        return {
            'user_id': request.session.get('user_id'),
            'locker_name': request.session.get('locker_name'),
            'email': request.session.get('email'),
            'root_id': request.session.get('root_id'),
            'session_created': request.session.get('session_created'),
        }
    return None

def clear_session(request: Request) -> None:
    """Clear the user session (logout)."""
    request.session.clear()
