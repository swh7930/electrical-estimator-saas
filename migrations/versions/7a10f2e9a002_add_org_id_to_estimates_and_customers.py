"""Add org_id to estimates and customers"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "7a10f2e9a002"
down_revision = "7a10f2e9a001"
branch_labels = None
depends_on = None

def upgrade():
    # estimates
    op.add_column("estimates", sa.Column("org_id", sa.Integer(), nullable=True))
    op.create_index("ix_estimates_org_id", "estimates", ["org_id"])
    op.create_foreign_key(
        "fk_estimates_org_id_orgs",
        "estimates", "orgs",
        ["org_id"], ["id"],
        ondelete="CASCADE",
    )

    # customers
    op.add_column("customers", sa.Column("org_id", sa.Integer(), nullable=True))
    op.create_index("ix_customers_org_id", "customers", ["org_id"])
    op.create_foreign_key(
        "fk_customers_org_id_orgs",
        "customers", "orgs",
        ["org_id"], ["id"],
        ondelete="CASCADE",
    )

def downgrade():
    op.drop_constraint("fk_customers_org_id_orgs", "customers", type_="foreignkey")
    op.drop_index("ix_customers_org_id", table_name="customers")
    op.drop_column("customers", "org_id")

    op.drop_constraint("fk_estimates_org_id_orgs", "estimates", type_="foreignkey")
    op.drop_index("ix_estimates_org_id", table_name="estimates")
    op.drop_column("estimates", "org_id")
