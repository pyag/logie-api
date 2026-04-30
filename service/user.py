import logging

from argon2 import PasswordHasher

from dbmodels.file_model import File
from dbmodels.locker_model import Locker
from enums import FileType

logger = logging.getLogger("uvicorn.debug")

async def emailExists(email: str) -> bool:
    """Check if the email already exists in the database."""
    return await Locker.filter(email=email).exists()

async def lockerNameExists(name: str) -> bool:
    """Check if the locker name already exists in the database."""
    return await Locker.filter(name=name).exists()

async def save(lname: str, pHash: str, email: str | None = None) -> Locker:
    """Save the locker to the database and return the created locker."""
    try:
        if lname:
            lname = lname.strip()
            if await lockerNameExists(lname):
                raise ValueError("Locker name already exists.")

        if email:
            email = email.strip()
            if await emailExists(email):
                raise ValueError("Email already exists.")

        locker = await Locker.create(name=lname, pwd=pHash, email=email)
        return locker
    except ValueError as ve:
        raise ve
    except Exception as e:
        raise e

async def authenticate(identifier: str, password: str) -> Locker | None:
    """Authenticate user by locker name or email and password."""
    ph = PasswordHasher()
    # Try locker name first
    locker = await Locker.filter(name=identifier).first()
    if not locker:
        # Try email
        locker = await Locker.filter(email=identifier).first()
    if locker:
        try:
            ph.verify(locker.pwd, password)
            return locker
        except Exception:
            return None
    return None

async def create_root_folder(locker: Locker) -> None:
    """Create the root folder for the locker."""

    try:
        logger.info(f"Creating root folder for locker: {locker.name} (ID: {locker.uid})")
        # Create the root folder for the locker
        await File.create(
            name="/",
            size=0,
            file_type=FileType.FOLDER,

            user=locker,
            parent=None,
        )
    except Exception as e:
        raise e
