"""S3-03b.2/3b add pattern_ops index on dje_items lower(description)

Revision ID: f65d530d3997
Revises: 254787ef749f
Create Date: 2025-10-08 07:40:21.247693

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f65d530d3997'
down_revision: Union[str, None] = '254787ef749f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Pattern-ops functional index to accelerate case-insensitive prefix searches:
      WHERE lower(description) LIKE 'scis%'
    Adds text_pattern_ops so planner uses an Index Scan for LIKE 'prefix%'.
    """
    op.create_index(
        "ix_dje_items_lower_description_pattern",
        "dje_items",
        [sa.text("lower(description) text_pattern_ops")],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_dje_items_lower_description_pattern", table_name="dje_items")
