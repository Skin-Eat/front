import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class BasketItem(Base):
    """API 명세서 v2 "장보기" — /basket/recommendations(routers/basket.py)는 그때그때
    계산만 하고 저장 안 하는 추천이고, 이건 사용자가 실제로 "내 리스트에 저장"한 것.
    같은 ingredient를 두 번 담으면 quantity를 올리는 정책인지 새 행을 만드는 정책인지는
    명세서에 명시 없음 — 지금은 새 행 허용(중복 방지 제약 없음), 필요해지면 unique(profile_id,
    ingredient_id)로 좁힐 것.
    """

    __tablename__ = "basket_item"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"))
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredient.id"))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    # 왜 담겼는지(예: "오메가3 부족" 같은 추천 사유) — 프론트 자유 텍스트, 서버는 검증 안 함
    reason: Mapped[str | None] = mapped_column(String(200), nullable=True)

    ingredient: Mapped["Ingredient"] = relationship()
