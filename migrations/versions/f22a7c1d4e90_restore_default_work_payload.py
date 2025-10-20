"""Restore default for estimates.work_payload to '{}'::jsonb

Revision ID: f22a7c1d4e90
Revises: ea1f2a3b4c5d
Create Date: 2025-10-19
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "f22a7c1d4e90"
down_revision = "ea1f2a3b4c5d"
branch_labels = None
depends_on = None

def upgrade():
    op.execute("ALTER TABLE estimates ALTER COLUMN work_payload SET DEFAULT '{}'::jsonb;")

def downgrade():
    op.execute("ALTER TABLE estimates ALTER COLUMN work_payload DROP DEFAULT;")
