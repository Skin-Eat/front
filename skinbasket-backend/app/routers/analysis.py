import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_profile_id
from app.db.session import get_db
from app.schemas.analysis import DeficiencyOut, NutrientAverageOut
from app.services.meal_query import get_recent_meal_logs
from app.services.skin_score import RECENT_WINDOW_DAYS, analyze_deficiency

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/deficiency", response_model=DeficiencyOut)
def get_deficiency(
    profile_id: uuid.UUID = Depends(get_current_profile_id),
    db: Session = Depends(get_db),
):
    """최근 7일 결핍 분석. 공통 지침 2.1: 점수/분석은 저장하지 않고 항상 조회 시점에 계산."""
    summary = analyze_deficiency(get_recent_meal_logs(db, profile_id))
    return DeficiencyOut(
        omega3=NutrientAverageOut(average=summary.omega3.average, sample_count=summary.omega3.sample_count),
        vit_c=NutrientAverageOut(average=summary.vit_c.average, sample_count=summary.vit_c.sample_count),
        vit_e=NutrientAverageOut(average=summary.vit_e.average, sample_count=summary.vit_e.sample_count),
        zinc=NutrientAverageOut(average=summary.zinc.average, sample_count=summary.zinc.sample_count),
        deficient_keys=summary.deficient_keys,
        high_sugar_meal_count=summary.high_sugar_meal_count,
        high_sat_fat_meal_count=summary.high_sat_fat_meal_count,
        window_days=RECENT_WINDOW_DAYS,
    )
