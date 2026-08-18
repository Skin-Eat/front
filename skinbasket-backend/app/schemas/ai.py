from pydantic import BaseModel

from app.schemas.recipe import RecipeIngredientOut


class FoodImageAnalysisResponse(BaseModel):
    """Android FoodImageAnalysisResponse.kt와 정확히 동일한 shape를 유지할 것."""

    candidates: list[str] = []


class AnalysisCommentResponse(BaseModel):
    """AI 역할 ②(분석 문장 생성)의 틀. DRAFT — 프론트가 이 shape를 그대로 쓸지 미확정."""

    comment: str


class AIRecipeSuggestionOut(BaseModel):
    """AI 역할 ③(레시피 생성)의 틀. schemas/recipe.py의 RecipeOut과 필드는 같지만
    DB에 저장된 id가 없다(즉석 생성이라 아직 recipe 테이블 row가 아님).
    DRAFT — 저장 여부가 정해지면 RecipeOut과 합쳐질 수도 있음."""

    name: str
    cooking_time_minutes: int
    servings: str
    ingredients: list[RecipeIngredientOut]
    steps: list[str]
    skin_benefits: list[dict]
