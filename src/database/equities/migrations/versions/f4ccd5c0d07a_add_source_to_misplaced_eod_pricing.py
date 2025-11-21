"""add_source_to_misplaced_eod_pricing

Revision ID: f4ccd5c0d07a
Revises: 4cdaf649fd57
Create Date: 2025-11-16 19:56:23.935041

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f4ccd5c0d07a'
down_revision: Union[str, Sequence[str], None] = '4cdaf649fd57'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add source column to misplaced_eod_pricing table
    op.add_column(
        'misplaced_eod_pricing',
        sa.Column(
            'source',
            postgresql.ENUM('EODHD', name='data_source_enum'),
            nullable=False,
            server_default='EODHD'  # Default value for existing rows
        )
    )
    # Remove server default after backfilling existing rows
    op.alter_column('misplaced_eod_pricing', 'source', server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    # Remove source column from misplaced_eod_pricing table
    op.drop_column('misplaced_eod_pricing', 'source')
