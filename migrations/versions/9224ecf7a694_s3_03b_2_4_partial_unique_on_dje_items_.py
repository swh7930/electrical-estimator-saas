"""S3-03b.2/4 partial UNIQUE on dje_items(category, description, vendor) where is_active

Revision ID: 9224ecf7a694
Revises: f65d530d3997
Create Date: 2025-10-08 07:46:55.797608

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9224ecf7a694'
down_revision: Union[str, None] = 'f65d530d3997'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Enforce: at most one ACTIVE catalog row per (category, description, vendor).
    Historical/inactive duplicates remain allowed.
    """
    op.create_index(
        "ux_dje_items_cat_desc_vendor_active_true",
        "dje_items",
        ["category", "description", "vendor"],
        unique=True,
        postgresql_where=sa.text("is_active = TRUE"),
    )


def downgrade() -> None:
    op.drop_index("ux_dje_items_cat_desc_vendor_active_true", table_name="dje_items")
