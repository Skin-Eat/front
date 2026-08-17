from datetime import datetime, time

from app.models.meal import MealType


def infer_meal_type(at: datetime) -> MealType:
    t = at.time()
    if t < time(11, 0):
        return MealType.BREAKFAST
    if t < time(15, 0):
        return MealType.LUNCH
    if t < time(18, 0):
        return MealType.SNACK
    return MealType.DINNER
