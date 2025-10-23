"""S3-03b.3a create org_memberships

Revision ID: 3144f5db25d3
Revises: 637e52cfce1d
Create Date: 2025-10-22 10:41:06.559201

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3144f5db25d3'
down_revision = '637e52cfce1d'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "org_memberships",
        sa.Column("id", sa.Integer(), primary_key=True),

        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),

        sa.Column("role", sa.String(length=20), nullable=False, server_default="member"),

        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),

        sa.ForeignKeyConstraint(["org_id"], ["orgs.id"], name="fk_org_memberships_org", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_org_memberships_user", ondelete="CASCADE"),
        sa.CheckConstraint("role IN ('owner','admin','member')", name="ck_org_memberships_role_valid"),
        sa.UniqueConstraint("org_id", "user_id", name="uq_org_memberships_org_user"),
    )

    op.create_index("ix_org_memberships_org_id", "org_memberships", ["org_id"])
    op.create_index("ix_org_memberships_user_id", "org_memberships", ["user_id"])


def downgrade():
    op.drop_index("ix_org_memberships_user_id", table_name="org_memberships")
    op.drop_index("ix_org_memberships_org_id", table_name="org_memberships")
    op.drop_table("org_memberships")