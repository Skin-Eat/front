import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, String, Uuid
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
    profile_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"))
    eaten_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    meal_type: Mapped[MealType] = mapped_column(Enum(MealType, name="meal_type"))
    # API 명세서 v2: photoConsent=false 유저는 안 보냄(프론트가 알아서 생략) — nullable.
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    items: Mapped[list["MealItem"]] = relationship(back_populates="meal_log", cascade="all, delete-orphan")


class MealItem(Base):
    __tablename__ = "meal_item"

    id: Mapped[int] = mapped_column(primary_key=True)
    meal_log_id: Mapped[int] = mapped_column(ForeignKey("meal_log.id", ondelete="CASCADE"))
    food_id: Mapped[int] = mapped_column(ForeignKey("food.id"))
    portion_ratio: Mapped[float] = mapped_column(Float, default=1.0)
    # AI 사진 인식으로 골라진 항목인지 — API 명세서 v2 items[].isAiDetected
    is_ai_detected: Mapped[bool] = mapped_column(Boolean, default=False)

    meal_log: Mapped[MealLog] = relationship(back_populates="items")
    # analyze_deficiency/score_for_item 등이 item.food.omega3_mg 식으로 접근하는데,
    # 이 relationship이 없어서 실제 데이터로 호출하면 AttributeError가 났었음 (누락 버그, 지금 수정).
    # "Food"를 문자열로만 참조 — food.py가 db.base를 import하고 db.base가 다시 모든 모델을
    # import하는 구조라, 여기서 Food를 직접 import하면 순환 임포트가 난다. SQLAlchemy가
    # 매퍼 구성 시점에 registry에서 이름으로 찾아 해결하므로 import 없이도 동작함.
    food: Mapped["Food"] = relationship()
