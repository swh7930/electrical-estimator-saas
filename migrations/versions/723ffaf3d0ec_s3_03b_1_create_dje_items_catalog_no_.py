"""S3-03b.1 create dje_items catalog (no unit_label)

Revision ID: 723ffaf3d0ec
Revises: 28c57b73c27a
Create Date: 2025-10-08 06:18:14.426469

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '723ffaf3d0ec'
down_revision: Union[str, None] = '28c57b73c27a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create DJE catalog table for estimating (no quantities; no unit_label).
    Holds stable facts used to populate the estimator's DJE dropdowns.
    - Quantities live in estimate-specific lines (will arrive in M3-C).
    - We avoid storing 'cost' totals; keep a default per-unit price here.
    """
    op.create_table(
        "dje_items",
        sa.Column("id", sa.Integer, primary_key=True, nullable=False),

        # Classification
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("subcategory", sa.String(), nullable=True),

        # Display / selection fields
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("vendor", sa.String(), nullable=True),

        # Default pricing used when adding to an estimate (can be overridden in-line)
        sa.Column("default_unit_cost", sa.Numeric(12, 4), nullable=False, server_default=sa.text("0")),

        # Lifecycle + audit
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("TRUE")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("default_unit_cost >= 0", name="chk_dje_items_unit_cost_nonneg"),
    )
    # No indexes here by design — we’ll add them in S3-03b.2+ as separate atomic steps.

def downgrade() -> None:
    op.drop_table("dje_items")
