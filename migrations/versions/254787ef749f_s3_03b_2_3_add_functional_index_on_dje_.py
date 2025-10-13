"""S3-03b.2/3 add functional index on dje_items lower(description)

Revision ID: 254787ef749f
Revises: 9c47853137c6
Create Date: 2025-10-08 07:34:16.133448

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '254787ef749f'
down_revision: Union[str, None] = '9c47853137c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Functional index to accelerate case-insensitive search/prefix filtering:
      WHERE lower(description) = 'scissor lift'
      WHERE lower(description) >= 'scis' AND lower(description) < 'scit'
    """
    op.create_index(
        "ix_dje_items_lower_description",
        "dje_items",
        [sa.text("lower(description)")],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_dje_items_lower_description", table_name="dje_items")
