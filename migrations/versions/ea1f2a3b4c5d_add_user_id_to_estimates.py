"""Add user_id to estimates

Revision ID: ea1f2a3b4c5d
Revises: c7d4e2f9a1b0
Create Date: 2025-10-19
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "ea1f2a3b4c5d"
down_revision = "c7d4e2f9a1b0"
branch_labels = None
depends_on = None

def upgrade():
    # 1) add column (nullable for now to avoid breaking existing rows)
    op.add_column("estimates", sa.Column("user_id", sa.Integer(), nullable=True))

    # 2) index for fast scoping
    op.create_index("ix_estimates_user_id", "estimates", ["user_id"])

    # 3) FK constraint to users(id)
    op.create_foreign_key(
        "fk_estimates_user_id_users",
        "estimates",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

def downgrade():
    op.drop_constraint("fk_estimates_user_id_users", "estimates", type_="foreignkey")
    op.drop_index("ix_estimates_user_id", table_name="estimates")
    op.drop_column("estimates", "user_id")
