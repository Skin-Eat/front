from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Recipe(Base):
    """DRAFT — ingredients/steps/skin_benefits를 JSONB로 접어서 테이블 수를 아꼈음
    (공통 지침의 "17->9 테이블 축소" 방향과 동일선상). 검색/필터링이 필요해지면
    그때 정규화된 테이블로 쪼갤 것. skin_benefits의 각 항목 문구는 인과 단정 표현
    금지(observed_pattern 톤 유지) — cause/because류 표현 넣지 말 것.
    """

    __tablename__ = "recipe"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    cooking_time_minutes: Mapped[int] = mapped_column(Integer)
    servings: Mapped[str] = mapped_column(String(30))
    ingredients: Mapped[list[str]] = mapped_column(JSONB, default=list)
    steps: Mapped[list[str]] = mapped_column(JSONB, default=list)
    # [{"nutrient": "오메가3", "description": "..."}]
    skin_benefits: Mapped[list[dict]] = mapped_column(JSONB, default=list)
