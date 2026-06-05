from pydantic import BaseModel

class SignupRequestModel(BaseModel):
    lockername: str
    password: str
    cnfrm_password: str
    email: str | None = None

class LoginRequestModel(BaseModel):
    identifier: str  # locker name or email
    password: str

class ChangePasswordRequestModel(BaseModel):
    current_password: str
    new_password: str

class DeleteLockerRequestModel(BaseModel):
    password: str

class LockerSearchItemModel(BaseModel):
    uid: str
    name: str
    root_id: str

class SearchLockerResponseModel(BaseModel):
    status_code: int
    message: str
    success: bool
    data: dict[str, list[LockerSearchItemModel]]
