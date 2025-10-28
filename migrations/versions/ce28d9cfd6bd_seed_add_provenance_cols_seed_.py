"""seed: add provenance cols + seed idempotency indexes (global + per-org)

Revision ID: ce28d9cfd6bd
Revises: 7ab9704b9caf
Create Date: 2025-10-28 09:30:12.124035

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ce28d9cfd6bd'
down_revision = '7ab9704b9caf'
branch_labels = None
depends_on = None


def upgrade():
    """ONLY: add seed provenance columns + seed idempotency indexes on existing tables."""
    # ---- materials: add columns ----
    op.add_column(
        'materials',
        sa.Column('is_seed', sa.Boolean(), server_default=sa.text('FALSE'), nullable=False),
    )
    op.add_column('materials', sa.Column('seed_pack', sa.String(), nullable=True))
    op.add_column('materials', sa.Column('seed_version', sa.Integer(), nullable=True))
    op.add_column('materials', sa.Column('seed_key', sa.String(), nullable=True))
    op.add_column(
        'materials',
        sa.Column('seeded_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
    )

    # ---- dje_items: add columns ----
    op.add_column(
        'dje_items',
        sa.Column('is_seed', sa.Boolean(), server_default=sa.text('FALSE'), nullable=False),
    )
    op.add_column('dje_items', sa.Column('seed_pack', sa.String(), nullable=True))
    op.add_column('dje_items', sa.Column('seed_version', sa.Integer(), nullable=True))
    op.add_column('dje_items', sa.Column('seed_key', sa.String(), nullable=True))
    op.add_column(
        'dje_items',
        sa.Column('seeded_at', postgresql.TIMESTAMP(timezone=True), nullable=True),
    )

    # ---- seed idempotency indexes (partial unique) ----
    # materials: unique per global seed (org_id IS NULL)
    op.create_index(
        'ux_materials_seed_key_global_true',
        'materials',
        ['seed_key'],
        unique=True,
        postgresql_where=sa.text('(is_seed = true) AND (org_id IS NULL)'),
    )
    # materials: unique per org seed (org_id IS NOT NULL)
    op.create_index(
        'ux_materials_org_seed_key_seeded_true',
        'materials',
        ['org_id', 'seed_key'],
        unique=True,
        postgresql_where=sa.text('(is_seed = true) AND (org_id IS NOT NULL)'),
    )
    # dje_items: unique per global seed
    op.create_index(
        'ux_dje_items_seed_key_global_true',
        'dje_items',
        ['seed_key'],
        unique=True,
        postgresql_where=sa.text('(is_seed = true) AND (org_id IS NULL)'),
    )
    # dje_items: unique per org seed
    op.create_index(
        'ux_dje_items_org_seed_key_seeded_true',
        'dje_items',
        ['org_id', 'seed_key'],
        unique=True,
        postgresql_where=sa.text('(is_seed = true) AND (org_id IS NOT NULL)'),
    )

def downgrade():
    """Revert ONLY the seed provenance additions."""
    # ---- drop indexes (reverse order) ----
    op.drop_index('ux_dje_items_org_seed_key_seeded_true', table_name='dje_items')
    op.drop_index('ux_dje_items_seed_key_global_true', table_name='dje_items')
    op.drop_index('ux_materials_org_seed_key_seeded_true', table_name='materials')
    op.drop_index('ux_materials_seed_key_global_true', table_name='materials')

    # ---- drop columns on dje_items ----
    op.drop_column('dje_items', 'seeded_at')
    op.drop_column('dje_items', 'seed_key')
    op.drop_column('dje_items', 'seed_version')
    op.drop_column('dje_items', 'seed_pack')
    op.drop_column('dje_items', 'is_seed')

    # ---- drop columns on materials ----
    op.drop_column('materials', 'seeded_at')
    op.drop_column('materials', 'seed_key')
    op.drop_column('materials', 'seed_version')
    op.drop_column('materials', 'seed_pack')
    op.drop_column('materials', 'is_seed')
