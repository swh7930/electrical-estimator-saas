"""S3-03b.10a — billing models

Revision ID: a4e5c7b90123
Revises: 156fcc5f1934
Create Date: 2025-10-23 15:30:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a4e5c7b90123'
down_revision = '156fcc5f1934'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'billing_customers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('org_id', sa.Integer(), nullable=False),
        sa.Column('stripe_customer_id', sa.String(length=64), nullable=False, unique=True),
        sa.Column('billing_email', sa.String(length=255), nullable=True),
        sa.Column('default_payment_method', sa.String(length=64), nullable=True),
        sa.Column('billing_address_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('tax_ids_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(['org_id'], ['orgs.id'], ondelete="RESTRICT"),
    )
    op.create_index('ix_billing_customers_org_id', 'billing_customers', ['org_id'])
    op.create_index('ix_billing_customers_stripe_customer_id', 'billing_customers', ['stripe_customer_id'], unique=True)

    op.create_table(
        'subscriptions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('org_id', sa.Integer(), nullable=False),
        sa.Column('stripe_subscription_id', sa.String(length=64), nullable=False, unique=True),
        sa.Column('product_id', sa.String(length=64), nullable=False),
        sa.Column('price_id', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default=sa.text("'incomplete'")),
        sa.Column('cancel_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('cancel_at_period_end', sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column('current_period_end', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column('entitlements_json', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column('updated_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(['org_id'], ['orgs.id'], ondelete="RESTRICT"),
        sa.UniqueConstraint('org_id', name='uq_subscriptions_org_id'),
    )
    op.create_index('ix_subscriptions_org_id', 'subscriptions', ['org_id'])
    op.create_index('ix_subscriptions_stripe_subscription_id', 'subscriptions', ['stripe_subscription_id'], unique=True)
    op.create_index('ix_subscriptions_product_id', 'subscriptions', ['product_id'])
    op.create_index('ix_subscriptions_price_id', 'subscriptions', ['price_id'])
    op.create_index('ix_subscriptions_status', 'subscriptions', ['status'])
    op.create_index('ix_subscriptions_current_period_end', 'subscriptions', ['current_period_end'])

    op.create_table(
        'billing_event_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('stripe_event_id', sa.String(length=255), nullable=False, unique=True),
        sa.Column('type', sa.String(length=80), nullable=False),
        sa.Column('signature_valid', sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('retries', sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column('notes', sa.String(length=255), nullable=True),
        sa.Column('processed_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', postgresql.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index('ix_billing_event_logs_stripe_event_id', 'billing_event_logs', ['stripe_event_id'], unique=True)
    op.create_index('ix_billing_event_logs_type', 'billing_event_logs', ['type'])


def downgrade():
    op.drop_index('ix_billing_event_logs_type', table_name='billing_event_logs')
    op.drop_index('ix_billing_event_logs_stripe_event_id', table_name='billing_event_logs')
    op.drop_table('billing_event_logs')

    op.drop_index('ix_subscriptions_current_period_end', table_name='subscriptions')
    op.drop_index('ix_subscriptions_status', table_name='subscriptions')
    op.drop_index('ix_subscriptions_price_id', table_name='subscriptions')
    op.drop_index('ix_subscriptions_product_id', table_name='subscriptions')
    op.drop_index('ix_subscriptions_stripe_subscription_id', table_name='subscriptions')
    op.drop_index('ix_subscriptions_org_id', table_name='subscriptions')
    op.drop_table('subscriptions')

    op.drop_index('ix_billing_customers_stripe_customer_id', table_name='billing_customers')
    op.drop_index('ix_billing_customers_org_id', table_name='billing_customers')
    op.drop_table('billing_customers')
