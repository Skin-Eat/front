import uuid
from datetime import datetime, time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.security import get_current_profile_id
from app.db.session import get_db
from app.models.food import Food
from app.models.meal import MealItem, MealLog
from app.schemas.meal import MealLogCreate, MealLogOut
from app.services.meal_type import infer_meal_type
from app.services.skin_score import recent_cutoff

router = APIRouter(prefix="/meals", tags=["meals"])


@router.post("", response_model=MealLogOut)
def register_meal(
    body: MealLogCreate,
    profile_id: uuid.UUID = Depends(get_current_profile_id),
    db: Session = Depends(get_db),
):
    food = db.get(Food, body.food_id)
    if food is None:
        raise HTTPException(status_code=404, detail="해당 food_id가 없습니다.")

    eaten_at = body.eaten_at or datetime.utcnow()
    meal_log = MealLog(
        profile_id=profile_id,
        eaten_at=eaten_at,
        meal_type=body.meal_type or infer_meal_type(eaten_at),
        items=[MealItem(food_id=body.food_id, portion_ratio=body.portion_ratio)],
    )
    db.add(meal_log)
    db.commit()
    db.refresh(meal_log)
    return meal_log


@router.get("", response_model=list[MealLogOut])
def list_meals(
    range: str = "today",  # "today" | "recent" (최근 7일)
    profile_id: uuid.UUID = Depends(get_current_profile_id),
    db: Session = Depends(get_db),
):
    query = (
        db.query(MealLog)
        .options(joinedload(MealLog.items).joinedload(MealItem.food))
        .filter(MealLog.profile_id == profile_id)
    )
    if range == "today":
        today = datetime.utcnow().date()
        query = query.filter(MealLog.eaten_at >= datetime.combine(today, time.min))
    elif range == "recent":
        query = query.filter(MealLog.eaten_at >= recent_cutoff())
    else:
        raise HTTPException(status_code=400, detail="range는 today 또는 recent만 지원합니다.")

    return query.order_by(MealLog.eaten_at.desc()).all()
