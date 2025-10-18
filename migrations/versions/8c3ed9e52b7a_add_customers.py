"""Add customers table

Revision ID: 8c3ed9e52b7a
Revises: 2b0a6d30a893
Create Date: 2025-10-18 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8c3ed9e52b7a'
down_revision = '2b0a6d30a893'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'customers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('primary_contact', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('city', sa.String(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('TRUE')),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
    )
    # Common filters/sorts
    op.create_index('ix_customers_city_active', 'customers', ['city', 'is_active'], unique=False)
    # Expression + partial unique
    op.execute("CREATE INDEX IF NOT EXISTS ix_customers_lower_name ON customers ((lower(name)));")
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ux_customers_lower_name_active_true
        ON customers ((lower(name)))
        WHERE (is_active = true);
    """)


def downgrade():
    op.execute("DROP INDEX IF EXISTS ux_customers_lower_name_active_true;")
    op.execute("DROP INDEX IF EXISTS ix_customers_lower_name;")
    op.drop_index('ix_customers_city_active', table_name='customers')
    op.drop_table('customers')
