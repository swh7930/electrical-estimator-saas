"""S3-03b.4 add users.email_verified_at

Revision ID: 156fcc5f1934
Revises: d5328dd90b4c
Create Date: 2025-10-23 07:15:05.492216

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '156fcc5f1934'
down_revision = 'd5328dd90b4c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True))


def downgrade():
    op.drop_column("users", "email_verified_at")
