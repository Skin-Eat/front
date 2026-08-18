import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.envelope import EnvelopeRoute
from app.core.security import get_current_profile_id
from app.db.session import get_db
from app.models.food import Food
from app.models.ingredient import Ingredient
from app.models.meal import MealItem, MealLog
from app.models.recipe import Recipe
from app.schemas.recipe import RecipeEatRequest, RecipeEatResult, RecipeGenerateOut, RecipeGenerateRequest, RecipeOut
from app.services.meal_type import infer_meal_type

router = APIRouter(prefix="/recipes", tags=["recipes"], route_class=EnvelopeRoute)


@router.get("", response_model=list[RecipeOut])
def list_recipes(db: Session = Depends(get_db)):
    """API 명세서 v2. 지금은 정렬/페이지네이션 없이 전부 반환 — recipe 테이블이 아직
    비어있음(15종 시드가 cooking_time_minutes/servings/skin_benefits 값 대기 중, README 참고).
    """
    return db.query(Recipe).order_by(Recipe.id).all()


@router.get("/{recipe_id}", response_model=RecipeOut)
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = db.get(Recipe, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="레시피가 없습니다.")
    return recipe


def _match_recipe_by_ingredients(db: Session, ingredient_names: list[str]) -> tuple[Recipe | None, bool]:
    """ingredientIds(장바구니 등에서 고른 재료)와 재료가 가장 많이 겹치는 큐레이션 레시피를
    DB에서 찾는다. AI로 새로 만들지 않음 — 원래 계획이 "장바구니 재료 -> DB의 기존 레시피
    매칭"이었음(AI 생성은 이 기능 범위가 아니었음, 대화 중 확인).
    겹치는 재료가 하나도 없으면(또는 recipe 테이블이 비어있으면) 그래도 뭔가는 보여주고
    두 번째 반환값(is_fallback)을 True로 — 빈 화면 방지(API 명세서 v2 4.④)."""
    curated = db.query(Recipe).filter(Recipe.generated_by == "curated").all()
    if not curated:
        return None, True

    wanted = set(ingredient_names)

    def overlap(recipe: Recipe) -> int:
        return len({item["name"] for item in recipe.ingredients} & wanted)

    best = max(curated, key=overlap)
    return best, overlap(best) == 0


@router.post("/generate", response_model=RecipeGenerateOut)
def generate_recipe(
    body: RecipeGenerateRequest,
    db: Session = Depends(get_db),
):
    """API 명세서 v2: 장바구니 등에서 고른 ingredientIds로 DB의 큐레이션 레시피 중
    가장 잘 맞는 것을 찾아 반환한다 (AI 호출 없음). 겹치는 재료가 하나도 없을 때만
    isFallback=true로 표시."""
    ingredients = db.query(Ingredient).filter(Ingredient.id.in_(body.ingredient_ids)).all()
    if not ingredients:
        raise HTTPException(status_code=404, detail="존재하지 않는 ingredient_id입니다.")
    ingredient_names = [ing.name for ing in ingredients]

    matched, is_fallback = _match_recipe_by_ingredients(db, ingredient_names)
    if matched is None:
        raise HTTPException(status_code=404, detail="추천할 레시피가 없습니다 (recipe 테이블이 비어있음).")

    return RecipeGenerateOut(**RecipeOut.model_validate(matched).model_dump(), is_fallback=is_fallback)


@router.post("/{recipe_id}/eat", response_model=RecipeEatResult)
def eat_recipe(
    recipe_id: int,
    body: RecipeEatRequest = RecipeEatRequest(),
    profile_id: uuid.UUID = Depends(get_current_profile_id),
    db: Session = Depends(get_db),
):
    """폐쇄 루프의 마지막 연결고리: 먹는다 -> 기록 -> (재)분석.

    DRAFT: recipe.ingredients(`[{"name","amount"}]`)의 name을 food 테이블 이름과
    매칭해서 meal_log를 자동 생성한다. 이름이 정확히 안 맞으면 매칭에서 빠짐 — 나중에
    recipe<->food를 ID로 직접 연결하는 매핑 테이블/컬럼으로 바꾸는 게 더 견고함
    (지금은 "기반"만 잡아둔 것). 이 호출 이후 /analysis/diet, /basket/recommendations를
    다시 조회하면 갱신된 결과가 나오는 것으로 "차트가 갱신된다"는 요구를 충족한다 (별도 캐시 없음).
    """
    recipe = db.get(Recipe, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="레시피가 없습니다.")

    ingredient_names = [item["name"] for item in recipe.ingredients]
    matched_foods = db.query(Food).filter(Food.name.in_(ingredient_names)).all()
    if not matched_foods:
        return RecipeEatResult(logged_meal_ids=[], message="레시피 재료와 매칭되는 food가 없어 기록을 만들지 못했습니다.")

    eaten_at = body.eaten_at or datetime.utcnow()
    meal_log = MealLog(
        profile_id=profile_id,
        eaten_at=eaten_at,
        meal_type=body.meal_type or infer_meal_type(eaten_at),
        items=[MealItem(food_id=food.id, portion_ratio=body.portion_ratio) for food in matched_foods],
    )
    db.add(meal_log)
    db.commit()
    db.refresh(meal_log)

    return RecipeEatResult(
        logged_meal_ids=[meal_log.id],
        message=f"'{recipe.name}' 섭취를 기록했습니다. 분석 결과가 곧 반영됩니다.",
    )
