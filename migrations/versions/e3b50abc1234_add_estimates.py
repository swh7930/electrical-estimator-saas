"""Add estimates table

Revision ID: e3b50abc1234
Revises: 9f21ddc6c2c3
Create Date: 2025-10-19 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e3b50abc1234'
down_revision = '9f21ddc6c2c3'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'estimates',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('customer_id', sa.Integer(), nullable=True, index=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('project_address', sa.String(length=255), nullable=True),
        sa.Column('project_ref', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False, server_default=sa.text("'draft'")),
        sa.Column('settings_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id']),
    )
    # Expression + btree indexes
    op.execute("CREATE INDEX IF NOT EXISTS ix_estimates_name ON estimates ((lower(name)));")
    op.create_index('ix_estimates_created_at', 'estimates', ['created_at'])

def downgrade():
    op.drop_index('ix_estimates_created_at', table_name='estimates')
    op.execute("DROP INDEX IF EXISTS ix_estimates_name;")
    op.drop_table('estimates')
