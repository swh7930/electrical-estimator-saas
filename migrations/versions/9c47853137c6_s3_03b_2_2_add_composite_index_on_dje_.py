"""S3-03b.2/2 add composite index on dje_items(category, subcategory, description)

Revision ID: 9c47853137c6
Revises: a32f3e1e3870
Create Date: 2025-10-08 07:19:24.639927

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c47853137c6'
down_revision: Union[str, None] = 'a32f3e1e3870'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Composite btree index to support:
      WHERE category = ? [AND subcategory = ?] AND is_active = TRUE
      ORDER BY description
    Enables ordered Index Scan for catalog list views.
    """
    op.create_index(
        "ix_dje_items_cat_sub_desc",
        "dje_items",
        ["category", "subcategory", "description"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_dje_items_cat_sub_desc", table_name="dje_items")
