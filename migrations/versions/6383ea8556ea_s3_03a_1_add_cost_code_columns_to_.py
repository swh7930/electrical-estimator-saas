"""S3-03a.1 add cost-code columns to materials

Revision ID: 6383ea8556ea
Revises: 34555746e79c
Create Date: 2025-10-07 11:31:02.936215

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6383ea8556ea'
down_revision: Union[str, None] = '34555746e79c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("materials", sa.Column("material_cost_code", sa.Text(), nullable=True))
    op.add_column("materials", sa.Column("mat_cost_code_desc", sa.Text(), nullable=True))
    op.add_column("materials", sa.Column("labor_cost_code", sa.Text(), nullable=True))
    op.add_column("materials", sa.Column("labor_cost_code_desc", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("materials", "labor_cost_code_desc")
    op.drop_column("materials", "labor_cost_code")
    op.drop_column("materials", "mat_cost_code_desc")
    op.drop_column("materials", "material_cost_code")
