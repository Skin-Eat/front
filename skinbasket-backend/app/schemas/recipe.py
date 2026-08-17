from pydantic import BaseModel, ConfigDict


class RecipeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    cooking_time_minutes: int
    servings: str
    ingredients: list[str]
    steps: list[str]
    skin_benefits: list[dict]


class RecipeEatResult(BaseModel):
    logged_meal_ids: list[int]
    message: str
