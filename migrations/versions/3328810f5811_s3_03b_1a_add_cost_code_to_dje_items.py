"""S3-03b.1a add cost_code to dje_items

Revision ID: 3328810f5811
Revises: 9224ecf7a694
Create Date: 2025-10-08 08:22:49.633636

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3328810f5811'
down_revision: Union[str, None] = '9224ecf7a694'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("dje_items", sa.Column("cost_code", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("dje_items", "cost_code")
