import logging
from datetime import datetime

from argon2 import PasswordHasher
from fastapi import APIRouter, Depends, HTTPException, Request, Query, status
from email_validator import validate_email, EmailNotValidError

from pydmodels.user_model import (
    SignupRequestModel,
    LoginRequestModel,
    ChangePasswordRequestModel,
    DeleteLockerRequestModel,
    SearchLockerResponseModel,
)
from service import user as user_service
from service import session as session_service
from service.auth import create_access_token
from service.session import get_current_user

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

        # Save the new locker to the database
        locker = await user_service.save(lname, pHash, email)

        # Create the root folder for the locker
        root_id = await user_service.create_root_folder(locker)

        # Create session with the returned locker
        session_service.create_session(request, locker, root_id)

        token = create_access_token({
            "user_id": str(locker.uid),
            "locker_name": locker.name,
            "email": locker.email or "",
            "root_id": root_id,
            "session_created": datetime.now().isoformat(),
        })

        return {
            "status_code": status.HTTP_201_CREATED,
            "message": "Signup successful!",
            "success": True,
            "data": {"token": token},
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
    if not req_body.identifier or not req_body.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Locker name/email and password are required.",
        )

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

        # Get the root folder ID for the locker
        root_id = await user_service.get_root_folder_id(locker)

        # Create session
        session_service.create_session(request, locker, root_id)

        token = create_access_token({
            "user_id": str(locker.uid),
            "locker_name": locker.name,
            "email": locker.email or "",
            "root_id": root_id,
            "session_created": datetime.now().isoformat(),
        })

        return {
            "status_code": status.HTTP_200_OK,
            "message": "Login successful!",
            "success": True,
            "data": {"token": token},
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
async def get_me(user: dict = Depends(get_current_user)):
    """Return the currently authenticated user from the session or token."""
    return {
        "status_code": status.HTTP_200_OK,
        "message": "User authenticated",
        "success": True,
        "data": user,
    }

@router.get('/search/', response_model=SearchLockerResponseModel)
async def search_lockers(name: str | None = Query(None, min_length=1, description="Locker name to search for")):
    """Search for lockers by name. Exact match results are returned first, then partial matches."""
    if not name or not name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search text is required.",
        )

    try:
        lockers = await user_service.search_lockers(name)
        return {
            "status_code": status.HTTP_200_OK,
            "message": "Search results",
            "success": True,
            "data": {
                "lockers": lockers,
            },
        }
    except Exception as e:
        logger.exception("Unexpected error during search")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during search.",
        )

@router.post('/change-password/')
async def change_password(body: ChangePasswordRequestModel, user: dict = Depends(get_current_user)):
    """Change the password for the currently authenticated user."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    if not body.current_password or not body.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password and new password are required.",
        )
    
    if body.current_password == body.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password cannot be the same as the current password.",
        )

    try:
        await user_service.change_password(user, body.current_password, body.new_password)
        return {
            "status_code": status.HTTP_200_OK,
            "message": "Password changed successfully",
            "success": True,
        }
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as e:
        logger.exception("Unexpected error during password change")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while changing the password.",
        )

@router.post('/delete-locker/')
async def delete_locker(body: DeleteLockerRequestModel, request: Request, user: dict = Depends(get_current_user)):
    """Delete the locker for the currently authenticated user."""

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    if not body.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required to delete locker.",
        )

    try:
        await user_service.delete_locker(user, body.password)
        if request is not None:
            session_service.clear_session(request)
        return {
            "status_code": status.HTTP_200_OK,
            "message": "Locker deleted successfully",
            "success": True,
        }
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve),
        )
    except Exception as e:
        logger.exception("Unexpected error during locker deletion")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while deleting the locker.",
        )
    

@router.post('/logout/')
async def logout(request: Request):
    """Clear the current session and log the user out."""
    session_service.clear_session(request)
    return {
        "status_code": status.HTTP_200_OK,
        "message": "Logged out successfully",
        "success": True,
    }
