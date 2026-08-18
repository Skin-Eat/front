from pydantic import Field

from app.models.ingredient import PriceBand
from app.schemas.base import CamelModel


class IngredientOut(CamelModel):
    id: int
    name: str
    key_nutrient: str
    purpose_tag: str
    search_keyword: str
    price_band: PriceBand | None
    appeal_note: str | None


class RecommendationGroupOut(CamelModel):
    key_nutrient: str
    is_deficient: bool
    primary: IngredientOut | None
    # API 명세서 v2: "supplements 최대 3" — routers/recommendations.py에서 자름
    subs: list[IngredientOut]


class RecommendationsOut(CamelModel):
    # API 명세서 v2: "최대 3개 그룹" — routers/recommendations.py에서 자름
    groups: list[RecommendationGroupOut]


class BasketItemIn(CamelModel):
    ingredient_id: int
    quantity: int = Field(ge=1, default=1)
    reason: str | None = None


class BasketItemUpdate(CamelModel):
    quantity: int = Field(ge=1)


class BasketItemOut(CamelModel):
    id: int
    quantity: int
    reason: str | None
    ingredient: IngredientOut
