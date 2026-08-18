import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.envelope import EnvelopeRoute
from app.core.security import get_current_profile_id
from app.db.session import get_db
from app.models.food import Food
from app.models.meal import MealItem, MealLog
from app.schemas.meal import AnalyzePhotoResponse, DetectedFoodOut, MealLogCreate, MealLogOut, MealLogUpdate
from app.services.meal_type import infer_meal_type
from app.services.openai_client import FoodRecognitionError, recognize_food

router = APIRouter(prefix="/meals", tags=["meals"], route_class=EnvelopeRoute)

_ANALYZE_PHOTO_MAX_CANDIDATES = 50


def _validate_food_ids(db: Session, food_ids: list[int]) -> None:
    found = set(db.scalars(select(Food.id).where(Food.id.in_(food_ids))).all())
    missing = set(food_ids) - found
    if missing:
        raise HTTPException(status_code=404, detail=f"존재하지 않는 food_id: {sorted(missing)}")


def _get_owned_meal(db: Session, meal_id: int, profile_id: uuid.UUID) -> MealLog:
    meal_log = (
        db.query(MealLog)
        .options(joinedload(MealLog.items).joinedload(MealItem.food))
        .filter(MealLog.id == meal_id, MealLog.profile_id == profile_id)
        .first()
    )
    if meal_log is None:
        raise HTTPException(status_code=404, detail="식사 기록이 없습니다.")
    return meal_log


@router.post("/analyze-photo", response_model=AnalyzePhotoResponse)
async def analyze_photo(image: UploadFile, db: Session = Depends(get_db)):
    """API 명세서 v2 — POST /ai/food-image(안드로이드가 이미 하드코딩한 구 계약,
    routers/ai.py에 그대로 남아있음)의 신규 버전. 차이점:
    1. 응답이 candidates:[문자열]이 아니라 detected:[{foodId,name,portionRatio}]
    2. 인식 실패를 502로 던지지 않고 success:true + aiFailed:true로 표현
       (명세서 0번 공통 규약: "AI 인식 실패" 같은 정상 상태는 에러가 아니라 플래그로)
    저장은 안 함(사진 인식만) — 실제 기록은 이 결과를 담아 POST /meals로 별도 호출."""
    candidate_names = db.scalars(select(Food.name).limit(_ANALYZE_PHOTO_MAX_CANDIDATES)).all()
    if not candidate_names:
        return AnalyzePhotoResponse(detected=[], ai_failed=True)

    image_bytes = await image.read()
    try:
        picked_names = await recognize_food(image_bytes, list(candidate_names))
    except FoodRecognitionError:
        return AnalyzePhotoResponse(detected=[], ai_failed=True)

    foods_by_name = {f.name: f for f in db.query(Food).filter(Food.name.in_(picked_names)).all()}
    detected = [
        DetectedFoodOut(food_id=foods_by_name[name].id, name=name, portion_ratio=1.0)
        for name in picked_names
        if name in foods_by_name
    ]
    return AnalyzePhotoResponse(detected=detected, ai_failed=False)


@router.post("", response_model=MealLogOut)
def register_meal(
    body: MealLogCreate,
    profile_id: uuid.UUID = Depends(get_current_profile_id),
    db: Session = Depends(get_db),
):
    """API 명세서 v2: 끼니당 여러 항목(items[])을 한 번에 등록 — 예전엔 food_id 하나만 됐음."""
    _validate_food_ids(db, [item.food_id for item in body.items])

    eaten_at = body.eaten_at or datetime.utcnow()
    meal_log = MealLog(
        profile_id=profile_id,
        eaten_at=eaten_at,
        meal_type=body.meal_type or infer_meal_type(eaten_at),
        photo_url=body.photo_url,
        items=[
            MealItem(food_id=item.food_id, portion_ratio=item.portion_ratio, is_ai_detected=item.is_ai_detected)
            for item in body.items
        ],
    )
    db.add(meal_log)
    db.commit()
    db.refresh(meal_log)
    return _get_owned_meal(db, meal_log.id, profile_id)


@router.get("", response_model=list[MealLogOut])
def list_meals(
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = None,
    profile_id: uuid.UUID = Depends(get_current_profile_id),
    db: Session = Depends(get_db),
):
    """API 명세서 v2: GET /meals?from=&to=. FastAPI 예약어 회피용으로 파이썬 파라미터명은
    from_지만 쿼리 파라미터 자체는 alias로 from을 그대로 받는다."""
    query = (
        db.query(MealLog)
        .options(joinedload(MealLog.items).joinedload(MealItem.food))
        .filter(MealLog.profile_id == profile_id)
    )
    if from_ is not None:
        query = query.filter(MealLog.eaten_at >= from_)
    if to is not None:
        query = query.filter(MealLog.eaten_at <= to)

    return query.order_by(MealLog.eaten_at.desc()).all()


@router.patch("/{meal_id}", response_model=MealLogOut)
def update_meal(
    meal_id: int,
    body: MealLogUpdate,
    profile_id: uuid.UUID = Depends(get_current_profile_id),
    db: Session = Depends(get_db),
):
    meal_log = _get_owned_meal(db, meal_id, profile_id)

    data = body.model_dump(exclude_unset=True, exclude={"items"})
    for field, value in data.items():
        setattr(meal_log, field, value)

    if body.items is not None:
        _validate_food_ids(db, [item.food_id for item in body.items])
        meal_log.items = [
            MealItem(food_id=item.food_id, portion_ratio=item.portion_ratio, is_ai_detected=item.is_ai_detected)
            for item in body.items
        ]

    db.commit()
    return _get_owned_meal(db, meal_id, profile_id)


@router.delete("/{meal_id}")
def delete_meal(
    meal_id: int,
    profile_id: uuid.UUID = Depends(get_current_profile_id),
    db: Session = Depends(get_db),
):
    meal_log = _get_owned_meal(db, meal_id, profile_id)
    db.delete(meal_log)
    db.commit()
    return None
