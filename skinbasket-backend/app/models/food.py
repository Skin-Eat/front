import enum

from sqlalchemy import Boolean, Enum, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class FoodSource(str, enum.Enum):
    MFDS = "MFDS"
    USER_ADDED = "USER_ADDED"


class Food(Base):
    """DRAFT — Android `Food.kt`와 1:1로 맞춰둔 상태. 필드를 늘리거나 줄일 때
    반드시 프론트 팀에도 알릴 것 (SkinScoreCalculator가 이 구조에 의존함).
    나트륨 컬럼은 아직 없음 (공통 지침 미확정 항목) — 추가 시 널값 처리 원칙(0 아님, 결측 제외) 지킬 것.
    """

    __tablename__ = "food"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    source: Mapped[FoodSource] = mapped_column(Enum(FoodSource, name="food_source"))
    serving_g: Mapped[int] = mapped_column(Integer)
    energy_kcal: Mapped[float] = mapped_column(Float)
    carb_g: Mapped[float] = mapped_column(Float)
    sugar_g: Mapped[float] = mapped_column(Float)
    protein_g: Mapped[float] = mapped_column(Float)
    fat_g: Mapped[float] = mapped_column(Float)

    # NULL = 데이터 없음. 0으로 취급 금지 (공통 지침 2.4)
    sat_fat_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    omega3_mg: Mapped[float | None] = mapped_column(Float, nullable=True)
    vit_a_ug: Mapped[float | None] = mapped_column(Float, nullable=True)
    vit_c_mg: Mapped[float | None] = mapped_column(Float, nullable=True)
    vit_e_mg: Mapped[float | None] = mapped_column(Float, nullable=True)
    zinc_mg: Mapped[float | None] = mapped_column(Float, nullable=True)

    is_dairy: Mapped[bool] = mapped_column(Boolean, default=False)
    is_high_gi: Mapped[bool] = mapped_column(Boolean, default=False)
