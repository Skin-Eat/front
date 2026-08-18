from app.models.profile import ConstraintType, SkinType
from app.schemas.base import CamelModel


class ConstraintIn(CamelModel):
    # 주의: API 명세서 v2는 값으로 "allergy"/"dislike"(소문자)를 쓰는데, ConstraintType enum은
    # DB/기존 코드와의 호환 때문에 아직 ALLERGY/DISLIKE(대문자)임 — 프론트와 대소문자 확인 필요.
    type: ConstraintType
    ingredient_name: str


class ConstraintOut(ConstraintIn):
    id: int


class ProfileUpdate(CamelModel):
    """PATCH /users/me — 보낸 필드만 갱신 (exclude_unset)."""

    nickname: str | None = None
    skin_type: SkinType | None = None
    concerns: list[str] | None = None
    photo_consent: bool | None = None
