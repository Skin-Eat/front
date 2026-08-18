from datetime import datetime

from pydantic import Field

from app.models.meal import MealType
from app.schemas.base import CamelModel


class MealItemIn(CamelModel):
    food_id: int
    # API 명세서 v2: 0 < x <= 10 (¼=0.25, ½=0.5, 1인분=1.0, 2인분=2.0 등)
    portion_ratio: float = Field(gt=0, le=10, default=1.0)
    is_ai_detected: bool = False


class MealLogCreate(CamelModel):
    eaten_at: datetime | None = None  # 비우면 서버가 now()로 채움
    meal_type: MealType | None = None  # 비우면 eaten_at 시각으로 추론
    photo_url: str | None = None
    items: list[MealItemIn] = Field(min_length=1)


class MealLogUpdate(CamelModel):
    """PATCH /meals/{id} — 보낸 필드만 갱신. items를 보내면 통째로 교체(부분 수정 아님)."""

    eaten_at: datetime | None = None
    meal_type: MealType | None = None
    photo_url: str | None = None
    items: list[MealItemIn] | None = None


class FoodOut(CamelModel):
    id: int
    name: str


class MealItemOut(CamelModel):
    id: int
    portion_ratio: float
    is_ai_detected: bool
    food: FoodOut


class MealLogOut(CamelModel):
    id: int
    eaten_at: datetime
    meal_type: MealType
    photo_url: str | None
    items: list[MealItemOut]


class DetectedFoodOut(CamelModel):
    food_id: int
    name: str
    portion_ratio: float = 1.0


class AnalyzePhotoResponse(CamelModel):
    """POST /meals/analyze-photo. 명세서 0번 공통 규약: AI 인식 실패는 4xx/5xx가 아니라
    success:true + aiFailed:true로 표현 — 라우터에서 예외를 던지지 않고 이 shape로 반환할 것."""

    detected: list[DetectedFoodOut]
    ai_failed: bool
