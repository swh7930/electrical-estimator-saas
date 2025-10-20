"""Add user_id to customers"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "ab91c2d3e4f5"
down_revision = "f22a7c1d4e90"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("customers", sa.Column("user_id", sa.Integer(), nullable=True))
    op.create_index("ix_customers_user_id", "customers", ["user_id"])
    op.create_foreign_key(
        "fk_customers_user_id_users",
        "customers",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )

def downgrade():
    op.drop_constraint("fk_customers_user_id_users", "customers", type_="foreignkey")
    op.drop_index("ix_customers_user_id", table_name="customers")
    op.drop_column("customers", "user_id")
