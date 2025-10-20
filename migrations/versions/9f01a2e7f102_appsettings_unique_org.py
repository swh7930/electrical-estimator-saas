"""Unique app_settings per org"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "9f01a2e7f102"
down_revision = "9f01a2e7f101"
branch_labels = None
depends_on = None

def upgrade():
    op.execute("DELETE FROM app_settings a USING app_settings b WHERE a.id > b.id AND a.org_id = b.org_id")
    op.create_unique_constraint("uq_app_settings_org", "app_settings", ["org_id"])

def downgrade():
    op.drop_constraint("uq_app_settings_org", "app_settings", type_="unique")
