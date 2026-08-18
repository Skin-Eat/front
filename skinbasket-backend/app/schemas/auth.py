import uuid

from pydantic import EmailStr

from app.models.profile import SkinType
from app.schemas.base import CamelModel


class SignupRequest(CamelModel):
    """API 명세서 v2는 skinType을 가입 시점 필수로 뒀지만, 실제 안드로이드 플로우는
    이메일/비밀번호/닉네임만으로 가입하고 skinType/concerns는 온보딩 화면에서 나중에
    PATCH /users/me로 채운다(README "인증 관련" 문서화된 시퀀싱 충돌의 (a)안으로 확정) —
    그래서 여기선 optional로 둠."""

    email: EmailStr
    password: str
    nickname: str
    skin_type: SkinType | None = None
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
