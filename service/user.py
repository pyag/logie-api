import logging

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from dbmodels.file_model import File
from dbmodels.locker_model import Locker
from enums import FileType
from logic.file import delete_file_from_storage

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

def delete_files_from_storage(files):
    """Delete files from storage based on their location field."""
    for file in files:
        if file.location and file.file_type != FileType.FOLDER:
            try:
                delete_file_from_storage(file.location)
            except Exception as e:
                # Log the error but continue to delete the database record
                logger.error(f"Failed to delete file at {file.location}, {e}")
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

async def create_root_folder(locker: Locker) -> str:
    """Create the root folder for the locker."""

    try:
        logger.info(f"Creating root folder for locker: {locker.name} (ID: {locker.uid})")
        # Create the root folder for the locker
        root = await File.create(
            name="/",
            size=0,
            file_type=FileType.FOLDER,

            user=locker,
            parent=None,
        )

        return str(root.uid)
    except Exception as e:
        raise e

async def get_root_folder_id(locker: Locker) -> str:
    """Get the root folder ID for the locker."""
    try:
        root = await File.filter(user=locker, parent=None).first()
        if not root:
            raise ValueError("Root folder not found for the locker.")

        return str(root.uid)
    except Exception as e:
        raise e

async def change_password(user, current_password, new_password) -> None:
    """Change the user's password after verifying the current password."""
    ph = PasswordHasher()
    try:
        print("Changing password for user: " + str(user))
        # Get the locker from the database
        locker = await Locker.filter(uid=user['user_id']).first()
        if not locker:
            raise ValueError("Locker not found.")

        # Verify current password
        try:
            ph.verify(locker.pwd, current_password)
        except VerifyMismatchError:
            raise ValueError("Current password is incorrect.")

        # Hash new password and update
        new_pHash = ph.hash(new_password)
        locker.pwd = new_pHash
        await locker.save()
    except Exception as e:
        raise e

async def delete_locker(user, password) -> None:
    """Delete the locker after verifying the password."""
    ph = PasswordHasher()
    try:
        # Get the locker from the database
        locker = await Locker.filter(uid=user['user_id']).first()
        if not locker:
            raise ValueError("Locker not found.")

        # Verify password
        try:
            ph.verify(locker.pwd, password)
        except VerifyMismatchError:
            raise ValueError("Password is incorrect.")

        locker_files = await File.filter(user=locker).all()
        delete_files_from_storage(locker_files)

        # Delete the locker (cascades to files/folders)
        await locker.delete()
    except Exception as e:
        raise e
