import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MealType(str, enum.Enum):
    BREAKFAST = "BREAKFAST"
    LUNCH = "LUNCH"
    DINNER = "DINNER"
    SNACK = "SNACK"


class MealLog(Base):
    """DRAFT — 끼니별 점수는 계산/저장하지 않는다 (공통 지침 2.1). 점수는 항상
    7일 조회 시점에 SkinScoreCalculator 상당 로직으로 계산 — score 컬럼을 여기에 추가하지 말 것.
    (단, Android 쪽은 오늘 하루치 점수는 예외적으로 프론트에서 별도 계산해 보여주기로 함 —
    백엔드가 그 값을 계산/저장해줄 필요는 없음)
    """

    __tablename__ = "meal_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"))
    eaten_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    meal_type: Mapped[MealType] = mapped_column(Enum(MealType, name="meal_type"))

    items: Mapped[list["MealItem"]] = relationship(back_populates="meal_log", cascade="all, delete-orphan")


class MealItem(Base):
    __tablename__ = "meal_item"

    id: Mapped[int] = mapped_column(primary_key=True)
    meal_log_id: Mapped[int] = mapped_column(ForeignKey("meal_log.id", ondelete="CASCADE"))
    food_id: Mapped[int] = mapped_column(ForeignKey("food.id"))
    portion_ratio: Mapped[float] = mapped_column(Float, default=1.0)

    meal_log: Mapped[MealLog] = relationship(back_populates="items")
