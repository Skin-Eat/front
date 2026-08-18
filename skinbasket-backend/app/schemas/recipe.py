import uuid

from pydantic import BaseModel, ConfigDict


class RecipeIngredientOut(BaseModel):
    name: str
    amount: str


class RecipeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: uuid.UUID | None
    name: str
    cooking_time_minutes: int
    servings: str
    ingredients: list[RecipeIngredientOut]
    steps: list[str]
    skin_benefits: list[dict]
    generated_by: str


class RecipeEatResult(BaseModel):
    logged_meal_ids: list[int]
    message: str
