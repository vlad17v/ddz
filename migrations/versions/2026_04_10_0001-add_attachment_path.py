"""add attachment path

Revision ID: 2026_04_10_0001
Revises: e50af0fcd9cc
Create Date: 2026-04-10 20:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_04_10_0001"
down_revision: Union[str, None] = "e50af0fcd9cc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("todos", sa.Column("attachment_path", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("todos", "attachment_path")
