"""add_threshold_counters_to_lows_and_rebounds

Revision ID: ae51e9228b5e
Revises: b40514cc7340
Create Date: 2025-11-27 11:18:03.337461

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ae51e9228b5e'
down_revision = 'b40514cc7340'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add number_of_high_thresholds column to lows and rebounds tables."""
    # Add number_of_high_thresholds to lows table
    op.add_column(
        'lows',
        sa.Column('number_of_high_thresholds', sa.Integer(), nullable=False, server_default='0'),
        schema='algorithms'
    )

    # Add number_of_high_thresholds to rebounds table
    op.add_column(
        'rebounds',
        sa.Column('number_of_high_thresholds', sa.Integer(), nullable=False, server_default='0'),
        schema='algorithms'
    )


def downgrade() -> None:
    """Remove number_of_high_thresholds column from lows and rebounds tables."""
    # Remove number_of_high_thresholds from rebounds table
    op.drop_column('rebounds', 'number_of_high_thresholds', schema='algorithms')

    # Remove number_of_high_thresholds from lows table
    op.drop_column('lows', 'number_of_high_thresholds', schema='algorithms')