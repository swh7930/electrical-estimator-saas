"""Add org_id to materials"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "af21c0f1f201"
down_revision = "9f01a2e7f102"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("materials", sa.Column("org_id", sa.Integer(), nullable=True))
    op.create_index("ix_materials_org_id", "materials", ["org_id"])
    op.create_foreign_key(
        "fk_materials_org_id_orgs",
        "materials", "orgs",
        ["org_id"], ["id"],
        ondelete="CASCADE",
    )

def downgrade():
    op.drop_constraint("fk_materials_org_id_orgs", "materials", type_="foreignkey")
    op.drop_index("ix_materials_org_id", table_name="materials")
    op.drop_column("materials", "org_id")
