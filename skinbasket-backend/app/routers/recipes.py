import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_profile_id
from app.db.session import get_db
from app.models.food import Food
from app.models.meal import MealItem, MealLog
from app.models.recipe import Recipe
from app.schemas.recipe import RecipeEatResult, RecipeOut
from app.services.meal_type import infer_meal_type

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.get("/{recipe_id}", response_model=RecipeOut)
def get_recipe(recipe_id: int, db: Session = Depends(get_db)):
    recipe = db.get(Recipe, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="레시피가 없습니다.")
    return recipe


@router.post("/{recipe_id}/eat", response_model=RecipeEatResult)
def eat_recipe(
    recipe_id: int,
    profile_id: uuid.UUID = Depends(get_current_profile_id),
    db: Session = Depends(get_db),
):
    """폐쇄 루프의 마지막 연결고리: 먹는다 -> 기록 -> (재)분석.

    DRAFT: recipe.ingredients(문자열 이름 목록)를 food 테이블 이름과 매칭해서 meal_log를
    자동 생성한다. 이름이 정확히 안 맞으면 매칭에서 빠짐 — 나중에 recipe<->food를
    ID로 직접 연결하는 매핑 테이블/컬럼으로 바꾸는 게 더 견고함 (지금은 "기반"만 잡아둔 것).
    이 호출 이후 /analysis/deficiency, /basket/recommendations를 다시 조회하면
    갱신된 결과가 나오는 것으로 "차트가 갱신된다"는 요구를 충족한다 (별도 캐시 없음).
    """
    recipe = db.get(Recipe, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="레시피가 없습니다.")

    matched_foods = db.query(Food).filter(Food.name.in_(recipe.ingredients)).all()
    if not matched_foods:
        return RecipeEatResult(logged_meal_ids=[], message="레시피 재료와 매칭되는 food가 없어 기록을 만들지 못했습니다.")

    now = datetime.utcnow()
    meal_log = MealLog(
        profile_id=profile_id,
        eaten_at=now,
        meal_type=infer_meal_type(now),
        items=[MealItem(food_id=food.id, portion_ratio=1.0) for food in matched_foods],
    )
    db.add(meal_log)
    db.commit()
    db.refresh(meal_log)

    return RecipeEatResult(
        logged_meal_ids=[meal_log.id],
        message=f"'{recipe.name}' 섭취를 기록했습니다. 분석 결과가 곧 반영됩니다.",
    )
