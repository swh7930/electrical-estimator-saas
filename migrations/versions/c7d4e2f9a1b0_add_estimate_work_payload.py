"""Add work_payload to estimates

Revision ID: c7d4e2f9a1b0
Revises: b3a9d1f8c7e2
Create Date: 2025-10-19
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "c7d4e2f9a1b0"
down_revision = "b3a9d1f8c7e2"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column(
        "estimates",
        sa.Column(
            "work_payload",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
    )
    # drop default after backfill safety
    op.execute("ALTER TABLE estimates ALTER COLUMN work_payload DROP DEFAULT;")

def downgrade():
    op.drop_column("estimates", "work_payload")
