import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_profile_id
from app.db.session import get_db
from app.models.profile import Profile, UserConstraint
from app.schemas.profile import ProfileCreate, ProfileOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/profile", response_model=ProfileOut)
def create_profile(
    body: ProfileCreate,
    profile_id: uuid.UUID = Depends(get_current_profile_id),
    db: Session = Depends(get_db),
):
    """온보딩 완료 시 1회 호출 — Android OnboardingScreen의 completeOnboarding()에 대응.
    Supabase Auth 가입 자체는 프론트가 처리하고, 여기서는 그 유저의 앱 전용 프로필만 만든다."""
    existing = db.get(Profile, profile_id)
    if existing is not None:
        raise HTTPException(status_code=409, detail="이미 프로필이 존재합니다.")

    profile = Profile(
        id=profile_id,
        nickname=body.nickname,
        skin_type=body.skin_type,
        concerns=body.concerns,
    )
    profile.constraints = [
        UserConstraint(type=c.type, ingredient_name=c.ingredient_name) for c in body.constraints
    ]
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/profile", response_model=ProfileOut)
def get_profile(
    profile_id: uuid.UUID = Depends(get_current_profile_id),
    db: Session = Depends(get_db),
):
    profile = db.get(Profile, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="프로필이 없습니다. 온보딩을 먼저 완료하세요.")
    return profile
