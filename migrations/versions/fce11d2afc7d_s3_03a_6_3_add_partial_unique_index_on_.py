"""S3-03a.6/3 add partial unique index on (material_type, item_description) where is_active

Revision ID: fce11d2afc7d
Revises: 98b8b5a4f041
Create Date: 2025-10-07 16:20:32.290960

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fce11d2afc7d'
down_revision: Union[str, None] = '98b8b5a4f041'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Enforce: at most one ACTIVE row per (material_type, item_description).
    Allows historical duplicates where is_active = FALSE.
    """
    op.create_index(
        "ux_materials_type_desc_active_true",   # name prefix 'ux' to denote uniqueness
        "materials",
        ["material_type", "item_description"],
        unique=True,
        postgresql_where=sa.text("is_active = TRUE"),  # partial (predicate) unique index
    )


def downgrade() -> None:
     op.drop_index("ux_materials_type_desc_active_true", table_name="materials")
