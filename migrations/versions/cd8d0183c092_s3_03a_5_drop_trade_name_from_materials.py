"""S3-03a.5 drop trade_name from materials

Revision ID: cd8d0183c092
Revises: da09370f322b
Create Date: 2025-10-07 12:09:08.346083

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cd8d0183c092'
down_revision: Union[str, None] = 'da09370f322b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
     op.drop_column("materials", "trade_name")


def downgrade() -> None:
    # Original was a character varying; Text is fine for rollback.
    op.add_column("materials", sa.Column("trade_name", sa.Text(), nullable=True))
