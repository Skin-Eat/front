import uuid

from pydantic import EmailStr

from app.models.profile import SkinType
from app.schemas.base import CamelModel


class SignupRequest(CamelModel):
    email: EmailStr
    password: str
    nickname: str
    skin_type: SkinType
    concerns: list[str] = []
    photo_consent: bool = False


class LoginRequest(CamelModel):
    email: EmailStr
    password: str


class UserOut(CamelModel):
    id: uuid.UUID
    nickname: str
    skin_type: SkinType | None
    concerns: list[str]
    photo_consent: bool


class AuthResponse(CamelModel):
    access_token: str
    user: UserOut
