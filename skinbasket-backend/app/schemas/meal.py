from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.meal import MealType


class MealLogCreate(BaseModel):
    food_id: int
    portion_ratio: float = 1.0
    eaten_at: datetime | None = None  # 비우면 서버가 now()로 채움
    meal_type: MealType | None = None  # 비우면 eaten_at 시각으로 추론


class FoodOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class MealItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    portion_ratio: float
    food: FoodOut


class MealLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    eaten_at: datetime
    meal_type: MealType
    items: list[MealItemOut]
