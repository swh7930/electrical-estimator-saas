"""S3-03a.3 enforce unit rule on materials

Revision ID: 8bba0b3f7dae
Revises: 6383ea8556ea
Create Date: 2025-10-07 11:50:23.317296

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8bba0b3f7dae'
down_revision: Union[str, None] = '6383ea8556ea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "chk_materials_unit",
        "materials",
        "unit_quantity_size IN (1, 100, 1000)"
    )
    op.alter_column("materials", "unit_quantity_size", existing_type=sa.Integer(), nullable=False)


def downgrade() -> None:
    op.alter_column("materials", "unit_quantity_size", existing_type=sa.Integer(), nullable=True)
    op.drop_constraint("chk_materials_unit", "materials", type_="check")
