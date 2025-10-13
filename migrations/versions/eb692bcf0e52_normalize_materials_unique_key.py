"""Normalize Materials unique key
- Drops: ux_materials_type_desc_active_true
- Creates: ux_materials_active_norm_key on
    (lower(trim(material_type)), lower(trim(item_description)))
  WHERE is_active = TRUE

Revision ID: eb692bcf0e52
Revises: 7a9c56c4c82e
Create Date: 2025-10-11 04:33:13.817080

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision: str = 'eb692bcf0e52'
down_revision: Union[str, None] = '7a9c56c4c82e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("DROP INDEX IF EXISTS ux_materials_type_desc_active_true;"))
    conn.execute(text("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_materials_active_norm_key
        ON materials (
          lower(trim(material_type)),
          lower(trim(item_description))
        )
        WHERE is_active = TRUE;
    """))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(text("DROP INDEX IF EXISTS ux_materials_active_norm_key;"))
    conn.execute(text("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_materials_type_desc_active_true
        ON materials (material_type, item_description)
        WHERE is_active = TRUE;
    """))
