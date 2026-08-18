import uuid

from sqlalchemy import JSON, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Recipe(Base):
    """DRAFT — ingredients/steps/skin_benefits를 JSONB로 접어서 테이블 수를 아꼈음
    (공통 지침의 "17->9 테이블 축소" 방향과 동일선상). 검색/필터링이 필요해지면
    그때 정규화된 테이블로 쪼갤 것. skin_benefits의 각 항목 문구는 인과 단정 표현
    금지(observed_pattern 톤 유지) — cause/because류 표현 넣지 말 것.

    AI/데이터 담당자가 준 시드 SQL(user_id/title/ingredients as {name,amount}/generated_by)과
    병합한 버전 — 다만 title은 그대로 name을 쓰기로 함(Android RecipeDetail.name과 일치).
    user_id=NULL이면 전체 큐레이션 레시피(generated_by="curated"), 값이 있으면
    그 유저를 위해 만들어진 레시피(예: generated_by="ai_generated" — services/openai_client.py의
    generate_recipe_suggestion 결과를 저장할 때 씀. 지금은 라우터에서 저장까지는 안 하고
    있으니 실제로 붙이려면 routers/ai.py의 recipe-suggestion 엔드포인트를 손볼 것).
    """

    __tablename__ = "recipe"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(100))
    cooking_time_minutes: Mapped[int] = mapped_column(Integer)
    servings: Mapped[str] = mapped_column(String(30))
    # [{"name": "연어", "amount": "150g"}]
    ingredients: Mapped[list[dict]] = mapped_column(JSON, default=list)
    steps: Mapped[list[str]] = mapped_column(JSON, default=list)
    # [{"nutrient": "오메가3", "description": "..."}]
    skin_benefits: Mapped[list[dict]] = mapped_column(JSON, default=list)
    # "curated" (user_id NULL) | "ai_generated" (user_id 있음)
    generated_by: Mapped[str] = mapped_column(String(20), default="curated")
