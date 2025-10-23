"""S3-03b.4 — Mail (Production Plan)

Revision ID: d5328dd90b4c
Revises: 3144f5db25d3
Create Date: 2025-10-23 07:12:39.409149

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd5328dd90b4c'
down_revision = '3144f5db25d3'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "email_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("to_email", sa.String(length=320), nullable=False),
        sa.Column("template", sa.String(length=64), nullable=False),
        sa.Column("subject", sa.String(length=200), nullable=False),
        sa.Column("provider_msg_id", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default=sa.text("'sent'")),
        sa.Column("meta", postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_email_logs_to_email", "email_logs", ["to_email"])
    op.create_index("ix_email_logs_provider_msg_id", "email_logs", ["provider_msg_id"])
    op.create_index("ix_email_logs_status", "email_logs", ["status"])



def downgrade():
    op.drop_index("ix_email_logs_status", table_name="email_logs")
    op.drop_index("ix_email_logs_provider_msg_id", table_name="email_logs")
    op.drop_index("ix_email_logs_to_email", table_name="email_logs")
    op.drop_table("email_logs")
