import logging

from argon2 import PasswordHasher
from fastapi import APIRouter, HTTPException, status, Request
from email_validator import validate_email, EmailNotValidError

from pydmodels.signup_model import SignupRequestModel, LoginRequestModel
from service import user as user_service
from service import session as session_service

logger = logging.getLogger("uvicorn.error")
router = APIRouter()

def hash_password(pwd: str) -> str:
    """Hash the password using a secure hashing algorithm."""

    ph = PasswordHasher()
    pHash = ph.hash(pwd)
    return pHash

def isValidEmail(email: str) -> str | None:
    try:
        """Validate the email format."""
        emailinfo = validate_email(email, check_deliverability=False)
        return emailinfo.normalized
    except EmailNotValidError:
        return None


def validate_request(req: SignupRequestModel):
    """Validate the signup request data."""
    if not req.lockername:
        raise ValueError("Locker name is required.")
    if not req.password:
        raise ValueError("Password is required.")
    if req.password != req.cnfrm_password:
        raise ValueError("Passwords do not match.")
    if req.email:
        validEmail = isValidEmail(req.email)
        if not validEmail:
            raise ValueError("Invalid email format.")
        req.email = validEmail


@router.post('/signup/', status_code=status.HTTP_201_CREATED)
async def signup(req_body: SignupRequestModel, request: Request):
    """Create a new locker with the given name and password."""

    try:
        validate_request(req_body)

        lname = req_body.lockername
        pwd = req_body.password
        email = req_body.email
        pHash = hash_password(pwd)

        logger.info(f"Signup request: lockername={lname}, email={email}")
        locker = await user_service.save(lname, pHash, email)

        # Create session with the returned locker
        session_service.create_session(request, locker)

        return {
            "status_code": status.HTTP_201_CREATED,
            "message": "Signup successful!",
            "success": True,
        }
    except ValueError as ve:
        logger.warning(f"Signup validation failed: {ve}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(ve),
        )
    except Exception as e:
        logger.exception("Unexpected error during signup")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during signup.",
        )

@router.post('/login/')
async def login(req_body: LoginRequestModel, request: Request):
    """Authenticate user and create session."""
    try:
        identifier = req_body.identifier.strip()
        password = req_body.password

        locker = await user_service.authenticate(identifier, password)
        if not locker:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="The locker name/email or password does not match.",
            )

        # Create session
        session_service.create_session(request, locker)

        return {
            "status_code": status.HTTP_200_OK,
            "message": "Login successful!",
            "success": True,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Unexpected error during login")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during login.",
        )

@router.get('/me/')
async def get_me(request: Request):
    """Return the currently authenticated user from the session."""
    user = session_service.get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    return {
        "status_code": status.HTTP_200_OK,
        "message": "User authenticated",
        "success": True,
        "data": user,
    }

@router.post('/logout/')
async def logout(request: Request):
    """Clear the current session and log the user out."""
    session_service.clear_session(request)
    return {
        "status_code": status.HTTP_200_OK,
        "message": "Logged out successfully",
        "success": True,
    }
