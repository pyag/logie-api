from dbmodels.locker_model import Locker

async def emailExists(email: str) -> bool:
    """Check if the email already exists in the database."""
    return await Locker.filter(email=email).exists()

async def lockerNameExists(name: str) -> bool:
    """Check if the locker name already exists in the database."""
    return await Locker.filter(name=name).exists()

async def save(lname: str, pHash: str, email: str | None = None) -> None:
    """Save the locker to the database."""
    try:
        if lname:
            lname = lname.strip()
            if await lockerNameExists(lname):
                raise ValueError("Locker name already exists.")

        if email:
            email = email.strip()
            if await emailExists(email):
                raise ValueError("Email already exists.")

        await Locker.create(name=lname, pwd=pHash, email=email)
    except ValueError as ve:
        raise ve
    except Exception as e:
        raise e
