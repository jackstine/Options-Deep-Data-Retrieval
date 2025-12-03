"""add_high_low_rebound_tables

Revision ID: 7e265fe22efc
Revises: 
Create Date: 2025-11-25 23:00:19.847319

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '7e265fe22efc'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create lows and rebounds tables for high/low algorithm."""
    # Create lows table
    # Note: No FK constraint on ticker_history_id - references equities-test database
    op.create_table(
        'lows',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('ticker_history_id', sa.Integer(), nullable=False),
        sa.Column('threshold', sa.Integer(), nullable=False),
        sa.Column('high_start_price', sa.BigInteger(), nullable=False),
        sa.Column('high_start_date', sa.Date(), nullable=False),
        sa.Column('low_threshold_price', sa.BigInteger(), nullable=True),
        sa.Column('low_threshold_date', sa.Date(), nullable=True),
        sa.Column('lowest_price', sa.BigInteger(), nullable=True),
        sa.Column('lowest_date', sa.Date(), nullable=True),
        sa.Column('high_threshold_price', sa.BigInteger(), nullable=True),
        sa.Column('high_threshold_date', sa.Date(), nullable=True),
        sa.Column('last_updated', sa.Date(), nullable=False),
        sa.Column('spawned', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('expired', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id', name='pk_lows')
    )

    # Create indexes for lows table
    op.create_index('ix_lows_ticker_history_id', 'lows', ['ticker_history_id'])
    op.create_index('ix_lows_threshold', 'lows', ['threshold'])
    op.create_index('ix_lows_last_updated', 'lows', ['last_updated'])
    op.create_index('ix_lows_expired', 'lows', ['expired'])

    # Create rebounds table
    # Note: No FK constraint on ticker_history_id - references equities-test database
    op.create_table(
        'rebounds',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('ticker_history_id', sa.Integer(), nullable=False),
        sa.Column('threshold', sa.Integer(), nullable=False),
        sa.Column('high_start_price', sa.BigInteger(), nullable=False),
        sa.Column('high_start_date', sa.Date(), nullable=False),
        sa.Column('low_threshold_price', sa.BigInteger(), nullable=False),
        sa.Column('low_threshold_date', sa.Date(), nullable=False),
        sa.Column('lowest_price', sa.BigInteger(), nullable=False),
        sa.Column('lowest_date', sa.Date(), nullable=False),
        sa.Column('high_threshold_price', sa.BigInteger(), nullable=False),
        sa.Column('high_threshold_date', sa.Date(), nullable=False),
        sa.Column('rebound_price', sa.BigInteger(), nullable=False),
        sa.Column('rebound_date', sa.Date(), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_rebounds')
    )

    # Create indexes for rebounds table
    op.create_index('ix_rebounds_ticker_history_id', 'rebounds', ['ticker_history_id'])
    op.create_index('ix_rebounds_threshold', 'rebounds', ['threshold'])
    op.create_index('ix_rebounds_low_threshold_date', 'rebounds', ['low_threshold_date'])
    op.create_index('ix_rebounds_rebound_date', 'rebounds', ['rebound_date'])


def downgrade() -> None:
    """Drop lows and rebounds tables."""
    op.drop_table('rebounds')
    op.drop_table('lows')
