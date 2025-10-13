"""S3-03c/3c: assemblies add category, subcategory, is_featured + filter indexes

Revision ID: 4561a77b2946
Revises: 927714721d56
Create Date: 2025-10-09 07:24:57.131154

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4561a77b2946'
down_revision: Union[str, None] = '927714721d56'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns
    op.add_column('assemblies', sa.Column('category', sa.Text(), nullable=True))
    op.add_column('assemblies', sa.Column('subcategory', sa.Text(), nullable=True))
    op.add_column('assemblies', sa.Column('is_featured', sa.Boolean(), nullable=False, server_default=sa.text('false')))

    # Partial indexes for quick filtering among active assemblies
    op.create_index(
        'ix_assemblies_category_active',
        'assemblies',
        [sa.text('lower(category)')],
        unique=False,
        postgresql_where=sa.text('is_active = true'),
        postgresql_using='btree'
    )
    op.create_index(
        'ix_assemblies_subcategory_active',
        'assemblies',
        [sa.text('lower(subcategory)')],
        unique=False,
        postgresql_where=sa.text('is_active = true'),
        postgresql_using='btree'
    )
    op.create_index(
        'ix_assemblies_category_subcategory_active',
        'assemblies',
        [sa.text('lower(category)'), sa.text('lower(subcategory)')],
        unique=False,
        postgresql_where=sa.text('is_active = true'),
        postgresql_using='btree'
    )


def downgrade() -> None:
    op.drop_index('ix_assemblies_category_subcategory_active', table_name='assemblies')
    op.drop_index('ix_assemblies_subcategory_active', table_name='assemblies')
    op.drop_index('ix_assemblies_category_active', table_name='assemblies')

    op.drop_column('assemblies', 'is_featured')
    op.drop_column('assemblies', 'subcategory')
    op.drop_column('assemblies', 'category')
