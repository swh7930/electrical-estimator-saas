"""S3-03b.8 F-3A: add org_id to dje_items

Revision ID: 32eda56478de
Revises: af21c0f1f201
Create Date: 2025-10-20 05:25:42.278791

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '32eda56478de'
down_revision = 'af21c0f1f201'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("dje_items", sa.Column("org_id", sa.Integer(), nullable=True))
    op.create_index("ix_dje_items_org_id", "dje_items", ["org_id"])
    op.create_foreign_key(
        "fk_dje_items_org_id_orgs",
        "dje_items", "orgs",
        ["org_id"], ["id"],
        ondelete="CASCADE",
    )


def downgrade():
    op.drop_constraint("fk_dje_items_org_id_orgs", "dje_items", type_="foreignkey")
    op.drop_index("ix_dje_items_org_id", table_name="dje_items")
    op.drop_column("dje_items", "org_id")
