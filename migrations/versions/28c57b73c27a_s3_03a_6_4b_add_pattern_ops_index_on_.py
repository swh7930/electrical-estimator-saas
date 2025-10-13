"""S3-03a.6/4b add pattern_ops index on lower(item_description)

Revision ID: 28c57b73c27a
Revises: 31dba1d06678
Create Date: 2025-10-07 16:33:04.625031

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '28c57b73c27a'
down_revision: Union[str, None] = '31dba1d06678'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Pattern-ops functional index to accelerate case-insensitive prefix searches:
      WHERE lower(item_description) LIKE 'emt%'
    Notes:
    - Using text_pattern_ops tells Postgres to use index ordering suitable for LIKE 'prefix%'.
    - We index the LOWER() value to match case-insensitive queries in the app.
    """
    op.create_index(
        "ix_materials_lower_item_description_pattern",
        "materials",
        [sa.text("lower(item_description) text_pattern_ops")],
        unique=False,
    )

def downgrade() -> None:
    op.drop_index("ix_materials_lower_item_description_pattern", table_name="materials")
