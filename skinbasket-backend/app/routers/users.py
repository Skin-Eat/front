import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.envelope import EnvelopeRoute
from app.core.security import get_current_profile_id
from app.db.session import get_db
from app.models.profile import Profile, UserConstraint
from app.schemas.auth import UserOut
from app.schemas.profile import ConstraintIn, ConstraintOut, ProfileUpdate

router = APIRouter(prefix="/users/me", tags=["users"], route_class=EnvelopeRoute)


@router.get("", response_model=UserOut)
def get_me(profile_id: uuid.UUID = Depends(get_current_profile_id), db: Session = Depends(get_db)):
    profile = db.get(Profile, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="프로필이 없습니다. 회원가입을 먼저 완료하세요.")
    return profile


@router.patch("", response_model=UserOut)
def update_me(
    body: ProfileUpdate,
    profile_id: uuid.UUID = Depends(get_current_profile_id),
    db: Session = Depends(get_db),
):
    profile = db.get(Profile, profile_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="프로필이 없습니다. 회원가입을 먼저 완료하세요.")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/constraints", response_model=list[ConstraintOut])
def list_constraints(profile_id: uuid.UUID = Depends(get_current_profile_id), db: Session = Depends(get_db)):
    return db.query(UserConstraint).filter(UserConstraint.profile_id == profile_id).all()


@router.post("/constraints", response_model=ConstraintOut)
def add_constraint(
    body: ConstraintIn,
    profile_id: uuid.UUID = Depends(get_current_profile_id),
    db: Session = Depends(get_db),
):
    constraint = UserConstraint(profile_id=profile_id, type=body.type, ingredient_name=body.ingredient_name)
    db.add(constraint)
    db.commit()
    db.refresh(constraint)
    return constraint


@router.delete("/constraints/{constraint_id}")
def delete_constraint(
    constraint_id: int,
    profile_id: uuid.UUID = Depends(get_current_profile_id),
    db: Session = Depends(get_db),
):
    constraint = db.get(UserConstraint, constraint_id)
    if constraint is None or constraint.profile_id != profile_id:
        raise HTTPException(status_code=404, detail="제약 조건이 없습니다.")
    db.delete(constraint)
    db.commit()
    return None
