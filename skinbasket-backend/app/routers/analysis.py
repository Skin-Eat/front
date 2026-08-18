import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.envelope import EnvelopeRoute
from app.core.security import get_current_profile_id
from app.db.session import get_db
from app.schemas.analysis import DeficiencyItemOut, DietAnalysisOut, NutrientAxisOut, ScoreOut
from app.services.meal_query import get_recent_meal_logs
from app.services.skin_score import analyze_deficiency, deficiency_ratio, logged_days, score_for_meals

router = APIRouter(prefix="/analysis", tags=["analysis"], route_class=EnvelopeRoute)

_LABELS = {"OMEGA3": "오메가3", "VIT_C": "비타민C", "VIT_E": "비타민E", "ZINC": "아연"}


def _build_summary(deficiencies: list[DeficiencyItemOut]) -> str:
    if not deficiencies:
        return "최근 식단이 비교적 균형 잡혀 있어요."
    top = deficiencies[0]
    label = _LABELS.get(top.code, top.code)
    if top.ratio is None:
        return f"최근 {label} 관련 식단 기록이 부족해요."
    return f"최근 {label} 섭취가 권장량의 {round(top.ratio * 100)}% 수준입니다."


@router.get("/diet", response_model=DietAnalysisOut)
def get_diet_analysis(
    days: int = 7,
    profile_id: uuid.UUID = Depends(get_current_profile_id),
    db: Session = Depends(get_db),
):
    """API 명세서 v2. 예전 GET /analysis/deficiency를 대체 — 응답 shape이 완전히 달라져서
    엔드포인트를 새로 만들지 않고 이 자리에서 바꿈(안드로이드가 아직 이 API를 안 부르고
    있어서 하위호환을 지킬 대상이 없음). 점수/결핍 모두 매 호출마다 계산하고 저장하지
    않는다(공통 지침 2.1 그대로)."""
    meal_logs = get_recent_meal_logs(db, profile_id, days=days)
    has_enough_data = logged_days(meal_logs) >= 3

    summary = analyze_deficiency(meal_logs)
    axes = [
        NutrientAxisOut(code=code, average=getattr(summary, code.lower()).average, is_deficient=is_def)
        for code, is_def in (
            ("OMEGA3", summary.omega3_deficient),
            ("VIT_C", summary.vit_c_deficient),
            ("VIT_E", summary.vit_e_deficient),
            ("ZINC", summary.zinc_deficient),
        )
    ]

    deficiencies = sorted(
        (
            DeficiencyItemOut(code=code, ratio=deficiency_ratio(code, axis.average), priority=0)
            for code, axis in zip(("OMEGA3", "VIT_C", "VIT_E", "ZINC"), axes)
            if axis.is_deficient
        ),
        key=lambda d: (d.ratio if d.ratio is not None else -1),
    )
    for i, item in enumerate(deficiencies, start=1):
        item.priority = i

    return DietAnalysisOut(
        has_enough_data=has_enough_data,
        score=ScoreOut(total=score_for_meals(meal_logs), axes=axes),
        deficiencies=deficiencies,
        summary=_build_summary(deficiencies),
        window_days=days,
    )
