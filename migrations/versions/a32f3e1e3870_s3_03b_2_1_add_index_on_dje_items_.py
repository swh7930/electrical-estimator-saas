"""S3-03b.2/1 add index on dje_items.category

Revision ID: a32f3e1e3870
Revises: 723ffaf3d0ec
Create Date: 2025-10-08 07:15:41.844068

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a32f3e1e3870'
down_revision: Union[str, None] = '723ffaf3d0ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Non-unique btree index on category to speed common filters:
      WHERE category = '...'
    """
    op.create_index(
        "ix_dje_items_category",
        "dje_items",
        ["category"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_dje_items_category", table_name="dje_items")
