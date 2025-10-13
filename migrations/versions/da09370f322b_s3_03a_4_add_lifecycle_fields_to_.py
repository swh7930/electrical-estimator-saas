"""S3-03a.4 add lifecycle fields to materials

Revision ID: da09370f322b
Revises: 8bba0b3f7dae
Create Date: 2025-10-07 12:00:27.492008

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'da09370f322b'
down_revision: Union[str, None] = '8bba0b3f7dae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("materials", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("materials", sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")))
    op.add_column("materials", sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")))


def downgrade() -> None:
    op.drop_column("materials", "updated_at")
    op.drop_column("materials", "created_at")
    op.drop_column("materials", "is_active")
