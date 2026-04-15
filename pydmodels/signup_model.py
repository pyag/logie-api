from pydantic import BaseModel

class SignupRequestModel(BaseModel):
    lockername: str
    password: str
    cnfrm_password: str
    email: str | None = None
