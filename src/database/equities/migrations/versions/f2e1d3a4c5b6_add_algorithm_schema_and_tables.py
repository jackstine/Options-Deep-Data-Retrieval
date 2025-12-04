"""add_algorithm_schema_and_tables

Revision ID: f2e1d3a4c5b6
Revises: cad15cbac7c8
Create Date: 2025-12-03 12:00:00.000000

This migration combines the algorithm database tables (lows, rebounds, highs, reversals)
into the equities database under a dedicated 'algorithm' schema for organization.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f2e1d3a4c5b6'
down_revision: Union[str, Sequence[str], None] = 'cad15cbac7c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create algorithm schema and migrate all algorithm tables to equities database."""
    # Create the algorithm schema
    op.execute('CREATE SCHEMA IF NOT EXISTS algorithm')

    # Create lows table for high/low algorithm
    # Note: No FK constraint on ticker_history_id - references ticker_history table in equities schema
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
        sa.Column('number_of_high_thresholds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_updated', sa.Date(), nullable=False),
        sa.Column('spawned', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('expired', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id', name='pk_lows'),
        schema='algorithm'
    )

    # Create indexes for lows table
    op.create_index('ix_lows_ticker_history_id', 'lows', ['ticker_history_id'], schema='algorithm')
    op.create_index('ix_lows_threshold', 'lows', ['threshold'], schema='algorithm')
    op.create_index('ix_lows_last_updated', 'lows', ['last_updated'], schema='algorithm')
    op.create_index('ix_lows_expired', 'lows', ['expired'], schema='algorithm')

    # Create rebounds table for completed high/low patterns
    # Note: No FK constraint on ticker_history_id - references ticker_history table in equities schema
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
        sa.Column('number_of_high_thresholds', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id', name='pk_rebounds'),
        schema='algorithm'
    )

    # Create indexes for rebounds table
    op.create_index('ix_rebounds_ticker_history_id', 'rebounds', ['ticker_history_id'], schema='algorithm')
    op.create_index('ix_rebounds_threshold', 'rebounds', ['threshold'], schema='algorithm')
    op.create_index('ix_rebounds_low_threshold_date', 'rebounds', ['low_threshold_date'], schema='algorithm')
    op.create_index('ix_rebounds_rebound_date', 'rebounds', ['rebound_date'], schema='algorithm')

    # Create highs table for low/high algorithm
    # Note: No FK constraint on ticker_history_id - references ticker_history table in equities schema
    op.create_table(
        'highs',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('ticker_history_id', sa.Integer(), nullable=False),
        sa.Column('threshold', sa.Integer(), nullable=False),
        sa.Column('low_start_price', sa.BigInteger(), nullable=False),
        sa.Column('low_start_date', sa.Date(), nullable=False),
        sa.Column('high_threshold_price', sa.BigInteger(), nullable=True),
        sa.Column('high_threshold_date', sa.Date(), nullable=True),
        sa.Column('highest_price', sa.BigInteger(), nullable=True),
        sa.Column('highest_date', sa.Date(), nullable=True),
        sa.Column('low_threshold_price', sa.BigInteger(), nullable=True),
        sa.Column('low_threshold_date', sa.Date(), nullable=True),
        sa.Column('number_of_low_thresholds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_updated', sa.Date(), nullable=False),
        sa.Column('spawned', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('expired', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id', name='pk_highs'),
        schema='algorithm'
    )

    # Create indexes for highs table
    op.create_index('ix_highs_ticker_history_id', 'highs', ['ticker_history_id'], schema='algorithm')
    op.create_index('ix_highs_threshold', 'highs', ['threshold'], schema='algorithm')
    op.create_index('ix_highs_last_updated', 'highs', ['last_updated'], schema='algorithm')
    op.create_index('ix_highs_expired', 'highs', ['expired'], schema='algorithm')

    # Create reversals table for completed low/high patterns
    # Note: No FK constraint on ticker_history_id - references ticker_history table in equities schema
    op.create_table(
        'reversals',
        sa.Column('id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('ticker_history_id', sa.Integer(), nullable=False),
        sa.Column('threshold', sa.Integer(), nullable=False),
        sa.Column('low_start_price', sa.BigInteger(), nullable=False),
        sa.Column('low_start_date', sa.Date(), nullable=False),
        sa.Column('high_threshold_price', sa.BigInteger(), nullable=False),
        sa.Column('high_threshold_date', sa.Date(), nullable=False),
        sa.Column('highest_price', sa.BigInteger(), nullable=False),
        sa.Column('highest_date', sa.Date(), nullable=False),
        sa.Column('low_threshold_price', sa.BigInteger(), nullable=False),
        sa.Column('low_threshold_date', sa.Date(), nullable=False),
        sa.Column('reversal_price', sa.BigInteger(), nullable=False),
        sa.Column('reversal_date', sa.Date(), nullable=False),
        sa.Column('number_of_low_thresholds', sa.Integer(), nullable=False, server_default='0'),
        sa.PrimaryKeyConstraint('id', name='pk_reversals'),
        schema='algorithm'
    )

    # Create indexes for reversals table
    op.create_index('ix_reversals_ticker_history_id', 'reversals', ['ticker_history_id'], schema='algorithm')
    op.create_index('ix_reversals_threshold', 'reversals', ['threshold'], schema='algorithm')
    op.create_index('ix_reversals_high_threshold_date', 'reversals', ['high_threshold_date'], schema='algorithm')
    op.create_index('ix_reversals_reversal_date', 'reversals', ['reversal_date'], schema='algorithm')


def downgrade() -> None:
    """Drop algorithm tables and schema from equities database."""
    # Drop tables in reverse order
    op.drop_table('reversals', schema='algorithm')
    op.drop_table('highs', schema='algorithm')
    op.drop_table('rebounds', schema='algorithm')
    op.drop_table('lows', schema='algorithm')

    # Drop the schema
    op.execute('DROP SCHEMA IF EXISTS algorithm')
