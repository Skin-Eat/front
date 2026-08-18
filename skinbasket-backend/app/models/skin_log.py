import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SkinLog(Base):
    """DRAFT — 식단 데이터와 별개 도메인, 약 7일 시차로 연관짓는다는 원칙(공통 지침 2.4).
    photo_url은 Supabase Storage 경로/URL을 저장 (사진 자체를 DB에 넣지 않음).
    사진 저장 위치(서버 vs 기기)는 팀 미확정 항목 — 로컬 저장으로 바뀌면 이 컬럼이
    "업로드 여부 플래그" 정도로 축소될 수 있음.
    """

    __tablename__ = "skin_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    profile_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"))
    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    trouble_level: Mapped[int] = mapped_column(Integer)
    oil_level: Mapped[int] = mapped_column(Integer)
    dryness_level: Mapped[int] = mapped_column(Integer)
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    memo: Mapped[str | None] = mapped_column(String(300), nullable=True)
