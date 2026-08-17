import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_profile_id
from app.db.session import get_db
from app.models.ingredient import Ingredient
from app.schemas.basket import BasketRecommendationOut, RecommendationGroupOut
from app.services.meal_query import get_recent_meal_logs
from app.services.skin_score import analyze_deficiency

ALL_KEYS = ["OMEGA3", "VIT_C", "VIT_E", "ZINC"]

router = APIRouter(prefix="/basket", tags=["basket"])


@router.get("/recommendations", response_model=BasketRecommendationOut)
def get_recommendations(
    profile_id: uuid.UUID = Depends(get_current_profile_id),
    db: Session = Depends(get_db),
):
    """Android BasketScreen과 동일한 규칙: 부족한 축이 있으면 그것만, 없으면 4축 전부 보여줌."""
    summary = analyze_deficiency(get_recent_meal_logs(db, profile_id))
    active_keys = summary.deficient_keys or ALL_KEYS

    groups: list[RecommendationGroupOut] = []
    for key in active_keys:
        ingredients = db.query(Ingredient).filter(Ingredient.key_nutrient == key).all()
        primary = next((i for i in ingredients if i.is_primary), None)
        subs = [i for i in ingredients if not i.is_primary]
        groups.append(
            RecommendationGroupOut(
                key_nutrient=key,
                is_deficient=key in summary.deficient_keys,
                primary=primary,
                subs=subs,
            )
        )

    return BasketRecommendationOut(groups=groups)
