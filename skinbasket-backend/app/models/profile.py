import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SkinType(str, enum.Enum):
    OILY = "OILY"
    DRY = "DRY"
    COMBINATION = "COMBINATION"


class ConstraintType(str, enum.Enum):
    ALLERGY = "ALLERGY"
    DISLIKE = "DISLIKE"


class Profile(Base):
    """DRAFT — DB 설계 문서(v0.3, 9테이블)와 대조해서 필드명/타입 맞출 것.

    id는 Supabase Auth의 auth.users.id(UUID)를 그대로 재사용한다는 전제.
    비밀번호/이메일 자체는 Supabase Auth가 관리하므로 여기 저장하지 않는다.
    concerns는 users.concerns JSON 배열 결정을 그대로 반영 (Android SkinConcern enum과 값 동기화 필요).
    """

    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    nickname: Mapped[str] = mapped_column(String(50))
    skin_type: Mapped[SkinType | None] = mapped_column(Enum(SkinType, name="skin_type"), nullable=True)
    concerns: Mapped[list[str]] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    constraints: Mapped[list["UserConstraint"]] = relationship(back_populates="profile", cascade="all, delete-orphan")


class UserConstraint(Base):
    """allergy=강제 제외, dislike=대체재 우선 제안. Android ConstraintType과 동일."""

    __tablename__ = "user_constraint"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("profiles.id", ondelete="CASCADE"))
    type: Mapped[ConstraintType] = mapped_column(Enum(ConstraintType, name="constraint_type"))
    ingredient_name: Mapped[str] = mapped_column(String(100))

    profile: Mapped[Profile] = relationship(back_populates="constraints")
