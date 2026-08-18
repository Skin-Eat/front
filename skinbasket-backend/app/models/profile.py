import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SkinType(str, enum.Enum):
    # Android SkinType.kt와 값 맞춤 — 원래 3개(OILY/DRY/COMBINATION)만 있었는데 안드로이드는
    # NORMAL/COMBINATION_OILY까지 5개를 씀. 온보딩에서 그 값 그대로 넘어오면 검증에서
    # 튕겨나가서 여기도 5개로 맞춤 (분석 로직은 skin_type을 안 쓰므로 값 늘려도 안전함).
    OILY = "OILY"
    DRY = "DRY"
    NORMAL = "NORMAL"
    COMBINATION = "COMBINATION"
    COMBINATION_OILY = "COMBINATION_OILY"


class ConstraintType(str, enum.Enum):
    # 값(=JSON에 나가는 문자열)만 API 명세서 v2에 맞춰 소문자로 — 멤버 이름은 그대로라
    # 코드에서 ConstraintType.ALLERGY로 쓰는 곳은 안 바뀌어도 됨. SQLAlchemy Enum은 DB에
    # 멤버 "이름"(ALLERGY/DISLIKE)을 저장하므로 이 값 변경은 DB 마이그레이션도 필요 없음.
    ALLERGY = "allergy"
    DISLIKE = "dislike"


class Profile(Base):
    """DRAFT — DB 설계 문서(v0.3, 9테이블)와 대조해서 필드명/타입 맞출 것.

    id는 Supabase Auth의 auth.users.id(UUID)를 그대로 재사용한다는 전제.
    비밀번호/이메일 자체는 Supabase Auth가 관리하므로 여기 저장하지 않는다.
    concerns는 users.concerns JSON 배열 결정을 그대로 반영 (Android SkinConcern enum과 값 동기화 필요).
    """

    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    nickname: Mapped[str] = mapped_column(String(50))
    skin_type: Mapped[SkinType | None] = mapped_column(Enum(SkinType, name="skin_type"), nullable=True)
    concerns: Mapped[list[str]] = mapped_column(JSON, default=list)
    # 얼굴/피부 사진 수집·저장 동의 여부. false면 skin_log.photo_url 없이 수치만 기록 (API 명세서 v2).
    photo_consent: Mapped[bool] = mapped_column(Boolean, default=False)
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
