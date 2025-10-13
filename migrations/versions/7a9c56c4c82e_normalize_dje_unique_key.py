"""Normalize DJE unique key (case/trim + NULL-safe vendor)

- Drops: ux_dje_items_cat_desc_vendor_active_true
- Creates: ux_dje_items_active_norm_key on
    (lower(trim(category)), lower(trim(description)), coalesce(lower(trim(vendor)),''))
  WHERE is_active = TRUE

Revision ID: 7a9c56c4c82e
Revises: 4561a77b2946
Create Date: 2025-10-10 15:30:44.228468

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision: str = '7a9c56c4c82e'
down_revision: Union[str, None] = '4561a77b2946'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    conn = op.get_bind()
    conn.execute(text("DROP INDEX IF EXISTS ux_dje_items_cat_desc_vendor_active_true;"))
    conn.execute(text("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_dje_items_active_norm_key
        ON dje_items (
          lower(trim(category)),
          lower(trim(description)),
          coalesce(lower(trim(vendor)),'')
        )
        WHERE is_active = TRUE;
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("DROP INDEX IF EXISTS ux_dje_items_active_norm_key;"))
    conn.execute(text("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_dje_items_cat_desc_vendor_active_true
        ON dje_items (category, description, vendor)
        WHERE is_active = TRUE;
    """))