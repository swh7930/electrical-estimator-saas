"""Add org_id to app_settings and unique per org"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "9f01a2e7f101"
down_revision = "7a10f2e9a002"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("app_settings", sa.Column("org_id", sa.Integer(), nullable=True))
    op.create_index("ix_app_settings_org_id", "app_settings", ["org_id"])
    op.create_foreign_key(
        "fk_app_settings_org_id_orgs",
        "app_settings", "orgs",
        ["org_id"], ["id"],
        ondelete="CASCADE",
    )
    # allow multiple nulls during backfill; we'll add the unique after data is stamped

def downgrade():
    op.drop_constraint("fk_app_settings_org_id_orgs", "app_settings", type_="foreignkey")
    op.drop_index("ix_app_settings_org_id", table_name="app_settings")
    op.drop_column("app_settings", "org_id")
