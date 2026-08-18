"""expand skin_type enum

Revision ID: 497f957b7948
Revises: 188f0cff9f01
Create Date: 2026-08-19 00:16:11.885992

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '497f957b7948'
down_revision: Union[str, None] = '188f0cff9f01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # autogenerate가 Postgres enum에 값 추가하는 건 못 잡아내서 직접 씀.
    op.execute("ALTER TYPE skin_type ADD VALUE IF NOT EXISTS 'NORMAL'")
    op.execute("ALTER TYPE skin_type ADD VALUE IF NOT EXISTS 'COMBINATION_OILY'")


def downgrade() -> None:
    # Postgres는 enum 값 제거를 직접 지원 안 함(타입을 통째로 다시 만들어야 함) —
    # 지금 단계에서 그럴 필요는 없다고 판단해서 downgrade는 no-op으로 둠.
    pass
