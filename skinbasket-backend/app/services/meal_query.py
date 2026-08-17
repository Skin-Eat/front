import uuid

from sqlalchemy.orm import Session, joinedload

from app.models.meal import MealItem, MealLog
from app.services.skin_score import recent_cutoff


def get_recent_meal_logs(db: Session, profile_id: uuid.UUID) -> list[MealLog]:
    return (
        db.query(MealLog)
        .options(joinedload(MealLog.items).joinedload(MealItem.food))
        .filter(MealLog.profile_id == profile_id, MealLog.eaten_at >= recent_cutoff())
        .all()
    )
