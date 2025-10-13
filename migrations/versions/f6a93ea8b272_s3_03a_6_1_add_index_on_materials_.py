"""S3-03a.6/1 add index on materials.material_type

Purpose:
    Adds a performance index to speed up lookups by material_type.
    Used heavily by:
        • /api/material-types
        • /api/material_descriptions?type=<name>
    Safe, non-destructive, and reversible.

Verification steps:
    alembic upgrade head
    \d materials
    EXPLAIN ANALYZE SELECT ... WHERE material_type = '<Type>';

Revision ID: f6a93ea8b272
Revises: cd8d0183c092
Create Date: 2025-10-07 15:59:56.502769

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6a93ea8b272'
down_revision: Union[str, None] = 'cd8d0183c092'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create a non-unique btree index on materials.material_type.

    Notes:
    - Default PostgreSQL index type for text is btree.
    - No need to specify postgresql_using='btree'.
    - Keeps migration database-agnostic.
    """
    op.create_index(
        "ix_materials_material_type",  # index name
        "materials",                   # table name
        ["material_type"],              # column(s)
        unique=False
    )


def downgrade() -> None:
    """
    Drop the index to fully reverse this micro-step.
    """
    op.drop_index("ix_materials_material_type", table_name="materials")
