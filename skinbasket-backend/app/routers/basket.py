import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.core.envelope import EnvelopeRoute
from app.core.security import get_current_profile_id
from app.db.session import get_db
from app.models.basket_item import BasketItem
from app.models.ingredient import Ingredient
from app.schemas.basket import BasketItemIn, BasketItemOut, BasketItemUpdate

router = APIRouter(prefix="/basket", tags=["basket"], route_class=EnvelopeRoute)

# API 명세서 v2: 추천 계산(어떤 재료를 담을지)은 GET /recommendations/ingredients로 옮김
# (routers/recommendations.py). 여기는 사용자가 "내 리스트에 저장"한 것만 다룸
# (UI 문구도 "담기"가 아니라 "내 리스트에 저장" — 명세서 2.③ 참고). 새 basket_item 테이블.


@router.get("", response_model=list[BasketItemOut])
def list_basket_items(
    profile_id: uuid.UUID = Depends(get_current_profile_id),
    db: Session = Depends(get_db),
):
    return (
        db.query(BasketItem)
        .options(joinedload(BasketItem.ingredient))
        .filter(BasketItem.profile_id == profile_id)
        .order_by(BasketItem.id)
        .all()
    )


@router.post("/items", response_model=BasketItemOut)
def add_basket_item(
    body: BasketItemIn,
    profile_id: uuid.UUID = Depends(get_current_profile_id),
    db: Session = Depends(get_db),
):
    ingredient = db.get(Ingredient, body.ingredient_id)
    if ingredient is None:
        raise HTTPException(status_code=404, detail="해당 ingredient_id가 없습니다.")

    item = BasketItem(
        profile_id=profile_id,
        ingredient_id=body.ingredient_id,
        quantity=body.quantity,
        reason=body.reason,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.patch("/items/{item_id}", response_model=BasketItemOut)
def update_basket_item(
    item_id: int,
    body: BasketItemUpdate,
    profile_id: uuid.UUID = Depends(get_current_profile_id),
    db: Session = Depends(get_db),
):
    item = db.get(BasketItem, item_id)
    if item is None or item.profile_id != profile_id:
        raise HTTPException(status_code=404, detail="장바구니 항목이 없습니다.")
    item.quantity = body.quantity
    db.commit()
    db.refresh(item)
    return item


@router.delete("/items/{item_id}")
def delete_basket_item(
    item_id: int,
    profile_id: uuid.UUID = Depends(get_current_profile_id),
    db: Session = Depends(get_db),
):
    item = db.get(BasketItem, item_id)
    if item is None or item.profile_id != profile_id:
        raise HTTPException(status_code=404, detail="장바구니 항목이 없습니다.")
    db.delete(item)
    db.commit()
    return None


@router.delete("/items")
def clear_basket(
    profile_id: uuid.UUID = Depends(get_current_profile_id),
    db: Session = Depends(get_db),
):
    """전체 비우기 (API 명세서 v2)."""
    db.query(BasketItem).filter(BasketItem.profile_id == profile_id).delete()
    db.commit()
    return None
