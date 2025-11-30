"""add_data_quality_flags_to_ticker_history_stats

Revision ID: c3d850674719
Revises: f4ccd5c0d07a
Create Date: 2025-11-22 11:10:55.214514

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c3d850674719'
down_revision: str | Sequence[str] | None = 'f4ccd5c0d07a'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add data quality flag columns to ticker_history_stats table
    with op.batch_alter_table('ticker_history_stats', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('has_insufficient_coverage', sa.Boolean(), nullable=False, server_default='false')
        )
        batch_op.add_column(
            sa.Column('low_suspicious_price', sa.Boolean(), nullable=False, server_default='false')
        )
        batch_op.add_column(
            sa.Column('high_suspicious_price', sa.Boolean(), nullable=False, server_default='false')
        )
        # Add indexes for efficient filtering
        batch_op.create_index('ix_ticker_history_stats_has_insufficient_coverage', ['has_insufficient_coverage'])
        batch_op.create_index('ix_ticker_history_stats_low_suspicious_price', ['low_suspicious_price'])
        batch_op.create_index('ix_ticker_history_stats_high_suspicious_price', ['high_suspicious_price'])


def downgrade() -> None:
    """Downgrade schema."""
    # Remove data quality flag columns from ticker_history_stats table
    with op.batch_alter_table('ticker_history_stats', schema=None) as batch_op:
        batch_op.drop_index('ix_ticker_history_stats_high_suspicious_price')
        batch_op.drop_index('ix_ticker_history_stats_low_suspicious_price')
        batch_op.drop_index('ix_ticker_history_stats_has_insufficient_coverage')
        batch_op.drop_column('high_suspicious_price')
        batch_op.drop_column('low_suspicious_price')
        batch_op.drop_column('has_insufficient_coverage')
