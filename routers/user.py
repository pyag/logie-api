import logging

from argon2 import PasswordHasher
from fastapi import APIRouter, HTTPException, status
from email_validator import validate_email, EmailNotValidError

from pydmodels.signup_model import SignupRequestModel
from service import user as user_service

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
async def signup(req: SignupRequestModel):
    """Create a new locker with the given name and password."""

    try:
        validate_request(req)

        lname = req.lockername
        pwd = req.password
        email = req.email
        pHash = hash_password(pwd)

        logger.info(f"Signup request: lockername={lname}, email={email}")
        await user_service.save(lname, pHash, email)

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

@router.get("/users/")
async def list_users():
    """Return a listing of users in the system."""
    return {"users": ["hello", "world"]}
