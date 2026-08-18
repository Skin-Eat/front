import uuid
from datetime import datetime

from app.models.meal import MealType
from app.schemas.base import CamelModel


class RecipeIngredientOut(CamelModel):
    name: str
    amount: str


class RecipeOut(CamelModel):
    id: int
    user_id: uuid.UUID | None
    name: str
    cooking_time_minutes: int
    servings: str
    ingredients: list[RecipeIngredientOut]
    steps: list[str]
    skin_benefits: list[dict]
    generated_by: str


class RecipeGenerateRequest(CamelModel):
    ingredient_ids: list[int]


class RecipeGenerateOut(RecipeOut):
    # LLM 생성 실패 시 큐레이션 레시피로 대체 반환됐다는 표시 (API 명세서 v2 4.④)
    is_fallback: bool


class RecipeEatRequest(CamelModel):
    """POST /recipes/{id}/eat 바디 — 전부 선택값. 안 보내면 예전처럼 서버가 알아서 채움
    (now(), 시간대 추론, portionRatio=1.0 배율)."""

    eaten_at: datetime | None = None
    meal_type: MealType | None = None
    portion_ratio: float = 1.0


class RecipeEatResult(CamelModel):
    logged_meal_ids: list[int]
    message: str
