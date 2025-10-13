"""S3-03a.6/2 add composite index on materials(type,active,desc)

Revision ID: 98b8b5a4f041
Revises: f6a93ea8b272
Create Date: 2025-10-07 16:05:40.331695

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '98b8b5a4f041'
down_revision: Union[str, None] = 'f6a93ea8b272'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Composite btree index to support:
      WHERE material_type = ? AND is_active = TRUE
      ORDER BY item_description
    This lets the planner use a forward Index Scan in sorted order.
    """
    op.create_index(
        "ix_materials_type_active_desc",
        "materials",
        ["material_type", "is_active", "item_description"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_materials_type_active_desc", table_name="materials")
