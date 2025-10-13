"""S3-03a.6/4 add functional index on lower(item_description)

Revision ID: 31dba1d06678
Revises: fce11d2afc7d
Create Date: 2025-10-07 16:26:06.525610

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '31dba1d06678'
down_revision: Union[str, None] = 'fce11d2afc7d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Functional index to accelerate case-insensitive lookups and prefix searches:
      WHERE lower(item_description) = 'emt 1 in'
      WHERE lower(item_description) LIKE 'emt%'
    """
    op.create_index(
        "ix_materials_lower_item_description",
        "materials",
        [sa.text("lower(item_description)")],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_materials_lower_item_description", table_name="materials")
