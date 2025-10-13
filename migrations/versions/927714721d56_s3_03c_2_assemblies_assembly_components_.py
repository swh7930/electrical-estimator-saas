"""S3-03c/2: assemblies + assembly_components v1

Revision ID: 927714721d56
Revises: 3328810f5811
Create Date: 2025-10-08 16:40:23.159258

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '927714721d56'
down_revision: Union[str, None] = '3328810f5811'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # assemblies table
    op.create_table(
        'assemblies',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('assembly_code', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
    )

    # assembly_components table
    op.create_table(
        'assembly_components',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('assembly_id', sa.Integer(),
                  sa.ForeignKey('assemblies.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('material_id', sa.Integer(),
                  sa.ForeignKey('materials.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('qty_per_assembly', sa.Numeric(12, 4), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.CheckConstraint('qty_per_assembly > 0', name='ck_ac_qty_gt_zero'),
    )

    # ---- Indexes & partial uniques ----

    # assemblies: partial unique on lower(name) where is_active = true
    op.create_index(
        'uq_assemblies_lower_name_active_idx',
        'assemblies',
        [sa.text('lower(name)')],
        unique=True,
        postgresql_where=sa.text('is_active = true'),
        postgresql_using='btree'
    )

    # assembly_components: lookups + UI ordering
    op.create_index('ix_ac_assembly', 'assembly_components', ['assembly_id'], unique=False)
    op.create_index('ix_ac_material', 'assembly_components', ['material_id'], unique=False)
    op.create_index('ix_ac_assembly_sort', 'assembly_components', ['assembly_id', 'sort_order'], unique=False)

    # assembly_components: partial unique on (assembly_id, material_id) where active
    op.create_index(
        'uq_ac_assembly_material_active_idx',
        'assembly_components',
        ['assembly_id', 'material_id'],
        unique=True,
        postgresql_where=sa.text('is_active = true'),
        postgresql_using='btree'
    )


def downgrade() -> None:
    op.drop_index('uq_ac_assembly_material_active_idx', table_name='assembly_components')
    op.drop_index('ix_ac_assembly_sort', table_name='assembly_components')
    op.drop_index('ix_ac_material', table_name='assembly_components')
    op.drop_index('ix_ac_assembly', table_name='assembly_components')

    op.drop_index('uq_assemblies_lower_name_active_idx', table_name='assemblies')

    op.drop_table('assembly_components')
    op.drop_table('assemblies')
