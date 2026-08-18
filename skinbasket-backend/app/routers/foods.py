from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.envelope import EnvelopeRoute
from app.db.session import get_db
from app.models.food import Food, FoodSource
from app.schemas.food import FoodCreate, FoodOut

router = APIRouter(prefix="/foods", tags=["foods"], route_class=EnvelopeRoute)


@router.get("", response_model=list[FoodOut])
def search_foods(q: str = "", limit: int = 20, db: Session = Depends(get_db)):
    """API 명세서 v2: GET /foods?q=검색어&limit=20. 읽기 전용 참조 데이터라 recipes/{id}처럼
    인증 없이 열어둠."""
    query = db.query(Food)
    if q:
        query = query.filter(Food.name.ilike(f"%{q}%"))
    return query.order_by(Food.name).limit(min(limit, 50)).all()


@router.post("", response_model=FoodOut)
def create_food(body: FoodCreate, db: Session = Depends(get_db)):
    """없는 메뉴를 사용자가 직접 추가. FoodSource.USER_ADDED로 저장 — 세부 영양소는
    결측(NULL) 그대로 둬서 결핍 분석 평균에서 자동 제외됨(0으로 취급하지 않음)."""
    existing = db.query(Food).filter(Food.name == body.name).first()
    if existing is not None:
        raise HTTPException(status_code=409, detail="이미 있는 음식 이름입니다.")

    food = Food(
        name=body.name,
        source=FoodSource.USER_ADDED,
        serving_g=body.serving_g,
        energy_kcal=body.energy_kcal,
        carb_g=body.carb_g,
        sugar_g=body.sugar_g,
        protein_g=body.protein_g,
        fat_g=body.fat_g,
    )
    db.add(food)
    db.commit()
    db.refresh(food)
    return food
