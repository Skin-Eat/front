from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Alembic이 --autogenerate 할 때 모든 모델을 찾을 수 있도록 여기서 import.
# 새 모델 파일을 추가하면 반드시 아래에도 import를 추가할 것.
from app.models import basket_item, food, ingredient, meal, profile, recipe, skin_log  # noqa: E402,F401
