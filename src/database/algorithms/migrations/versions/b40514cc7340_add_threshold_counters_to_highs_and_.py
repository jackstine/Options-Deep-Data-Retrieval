"""add_threshold_counters_to_highs_and_reversals

Revision ID: b40514cc7340
Revises: 7b7bcab87f08
Create Date: 2025-11-27 11:14:28.249156

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b40514cc7340'
down_revision = '7b7bcab87f08'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add number_of_low_thresholds column to highs and reversals tables."""
    # Add number_of_low_thresholds to highs table
    op.add_column(
        'highs',
        sa.Column('number_of_low_thresholds', sa.Integer(), nullable=False, server_default='0'),
        schema='algorithms'
    )

    # Add number_of_low_thresholds to reversals table
    op.add_column(
        'reversals',
        sa.Column('number_of_low_thresholds', sa.Integer(), nullable=False, server_default='0'),
        schema='algorithms'
    )


def downgrade() -> None:
    """Remove number_of_low_thresholds column from highs and reversals tables."""
    # Remove number_of_low_thresholds from reversals table
    op.drop_column('reversals', 'number_of_low_thresholds', schema='algorithms')

    # Remove number_of_low_thresholds from highs table
    op.drop_column('highs', 'number_of_low_thresholds', schema='algorithms')