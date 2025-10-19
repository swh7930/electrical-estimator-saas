"""Align customers schema with Phase 2 spec

Revision ID: 9f21ddc6c2c3
Revises: 8c3ed9e52b7a
Create Date: 2025-10-18 15:45:00
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9f21ddc6c2c3'
down_revision = '8c3ed9e52b7a'
branch_labels = None
depends_on = None


def upgrade():
    # --- Add final spec columns ---
    op.add_column('customers', sa.Column('company_name', sa.String(), nullable=True))
    op.add_column('customers', sa.Column('contact_name', sa.String(), nullable=True))
    op.add_column('customers', sa.Column('address1', sa.String(), nullable=True))
    op.add_column('customers', sa.Column('address2', sa.String(), nullable=True))
    op.add_column('customers', sa.Column('state', sa.String(length=2), nullable=True))
    op.add_column('customers', sa.Column('zip', sa.String(length=10), nullable=True))
    # email, phone, city, notes, is_active, created_at, updated_at already exist

    # --- Indexes to add (keep existing ones; add missing best-practice) ---
    op.create_index('ix_customers_company_name', 'customers', ['company_name'], unique=False)
    op.create_index('ix_customers_contact_name', 'customers', ['contact_name'], unique=False)
    op.execute("CREATE INDEX IF NOT EXISTS ix_customers_lower_email ON customers ((lower(email)));")
    # Optional best-practice for scalable lists (safe to keep even if unused now)
    op.create_index('ix_customers_created_at', 'customers', ['created_at'], unique=False)

    # --- Drop legacy-only indexes before dropping legacy columns ---
    op.execute("DROP INDEX IF EXISTS ux_customers_lower_name_active_true;")
    op.execute("DROP INDEX IF EXISTS ix_customers_lower_name;")

    # --- Drop legacy columns (table is empty per user confirmation) ---
    with op.batch_alter_table('customers') as b:
        for col in ('name', 'primary_contact', 'address'):
            try:
                b.drop_column(col)
            except Exception:
                # If any legacy column doesn't exist, ignore safely
                pass


def downgrade():
    # Reverse best-effort: drop newly added indexes/columns
    op.drop_index('ix_customers_created_at', table_name='customers')
    op.execute("DROP INDEX IF EXISTS ix_customers_lower_email;")
    op.drop_index('ix_customers_contact_name', table_name='customers')
    op.drop_index('ix_customers_company_name', table_name='customers')

    with op.batch_alter_table('customers') as b:
        for col in ('zip', 'state', 'address2', 'address1', 'contact_name', 'company_name'):
            try:
                b.drop_column(col)
            except Exception:
                pass

    # We are not recreating legacy columns or legacy unique(index) on purpose.
