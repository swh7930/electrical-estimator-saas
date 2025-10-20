"""Create orgs table and add users.org_id"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "7a10f2e9a001"
down_revision = "ab91c2d3e4f5"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "orgs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.add_column("users", sa.Column("org_id", sa.Integer(), nullable=True))
    op.create_index("ix_users_org_id", "users", ["org_id"])
    op.create_foreign_key(
        "fk_users_org_id_orgs",
        "users", "orgs",
        ["org_id"], ["id"],
        ondelete="RESTRICT",
    )

def downgrade():
    op.drop_constraint("fk_users_org_id_orgs", "users", type_="foreignkey")
    op.drop_index("ix_users_org_id", table_name="users")
    op.drop_column("users", "org_id")
    op.drop_table("orgs")
