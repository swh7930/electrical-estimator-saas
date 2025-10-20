"""Add users table

Revision ID: b3a9d1f8c7e2
Revises: e3b50abc1234
Create Date: 2025-10-19
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "b3a9d1f8c7e2"
down_revision = "e3b50abc1234"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    # Case-insensitive unique email
    op.execute("CREATE UNIQUE INDEX ux_users_lower_email ON users (lower(email));")

def downgrade():
    op.execute("DROP INDEX IF EXISTS ux_users_lower_email;")
    op.drop_table("users")
