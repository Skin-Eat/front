import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.envelope import EnvelopeRoute
from app.core.security import get_current_profile_id
from app.db.session import get_db
from app.models.ingredient import Ingredient
from app.schemas.basket import IngredientOut, RecommendationGroupOut, RecommendationsOut
from app.services.meal_query import get_recent_meal_logs
from app.services.skin_score import analyze_deficiency, deficiency_ratio

ALL_KEYS = ["OMEGA3", "VIT_C", "VIT_E", "ZINC"]
MAX_GROUPS = 3
MAX_SUBS = 3

router = APIRouter(prefix="/recommendations", tags=["recommendations"], route_class=EnvelopeRoute)


@router.get("/ingredients", response_model=RecommendationsOut)
def get_ingredient_recommendations(
    profile_id: uuid.UUID = Depends(get_current_profile_id),
    db: Session = Depends(get_db),
):
    """API 명세서 v2: ②(GET /analysis/diet)의 deficiencies 기반, 최대 3개 그룹,
    그룹당 primary 1 + supplements 최대 3.

    예전 `/basket/recommendations`를 이 경로로 옮긴 것. "부족 없으면 4축 전부 보여줌"이던
    기존 규칙(Android BasketScreen과 동일하게 맞춰뒀던 것)은 "최대 3개 그룹" 캡과 충돌해서
    부족이 없을 때는 (부족 판정 임계값에 가장 가까운 순으로) 3축만 보여주는 쪽으로 바꿨다.
    """
    summary = analyze_deficiency(get_recent_meal_logs(db, profile_id))

    def sort_key(key: str) -> float:
        average = getattr(summary, key.lower()).average
        ratio = deficiency_ratio(key, average)
        return ratio if ratio is not None else -1  # 데이터 없음 = 가장 부족한 것으로 취급

    active_keys = sorted(summary.deficient_keys or ALL_KEYS, key=sort_key)[:MAX_GROUPS]

    groups: list[RecommendationGroupOut] = []
    for key in active_keys:
        ingredients = db.query(Ingredient).filter(Ingredient.key_nutrient == key).all()
        primary = next((i for i in ingredients if i.is_primary), None)
        subs = [i for i in ingredients if not i.is_primary][:MAX_SUBS]
        groups.append(
            RecommendationGroupOut(
                key_nutrient=key,
                is_deficient=key in summary.deficient_keys,
                primary=IngredientOut.model_validate(primary) if primary else None,
                subs=[IngredientOut.model_validate(sub) for sub in subs],
            )
        )

    return RecommendationsOut(groups=groups)
