from pydantic import BaseModel, ConfigDict

from app.models.ingredient import PriceBand


class IngredientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    key_nutrient: str
    purpose_tag: str
    search_keyword: str
    is_primary: bool
    price_band: PriceBand | None
    appeal_note: str | None


class RecommendationGroupOut(BaseModel):
    key_nutrient: str
    is_deficient: bool
    primary: IngredientOut | None
    subs: list[IngredientOut]


class BasketRecommendationOut(BaseModel):
    groups: list[RecommendationGroupOut]
