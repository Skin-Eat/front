import enum

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PriceBand(str, enum.Enum):
    LOW = "LOW"
    MID = "MID"
    HIGH = "HIGH"


class Ingredient(Base):
    """DRAFT — Skin Basket 추천 목록. Android `IngredientSeedData`와 값 동기화 필요.
    key_nutrient는 SkinScoreCalculator의 4축 키(OMEGA3/VIT_C/VIT_E/ZINC)와 문자열로 일치해야 함.
    "대체재"가 아니라 "보충 옵션"이라는 용어 원칙(공통 지침) — is_primary=false 항목을 프론트에서
    "alternatives"가 아니라 "supplements/subs"로 부르는 이유가 여기서 비롯됨.
    """

    __tablename__ = "ingredient"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    key_nutrient: Mapped[str] = mapped_column(String(20), index=True)
    # Android Ingredient.kt와 이름 맞춤: purposeTag/searchKeyword
    purpose_tag: Mapped[str] = mapped_column(String(100))
    search_keyword: Mapped[str] = mapped_column(String(200))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    price_band: Mapped[PriceBand | None] = mapped_column(Enum(PriceBand, name="price_band"), nullable=True)
    appeal_note: Mapped[str | None] = mapped_column(String(100), nullable=True)
