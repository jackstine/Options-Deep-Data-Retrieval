"""add_low_high_reversal_tables

Revision ID: 7b7bcab87f08
Revises: 7e265fe22efc
Create Date: 2025-11-26 23:31:30.271789

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7b7bcab87f08'
down_revision = '7e265fe22efc'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create highs and reversals tables for low/high algorithm."""
    # Create highs table
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
        sa.Column('last_updated', sa.Date(), nullable=False),
        sa.Column('spawned', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('expired', sa.Boolean(), nullable=False, server_default='false'),
        sa.ForeignKeyConstraint(
            ['ticker_history_id'],
            ['equities.ticker_history.id'],
            name='fk_highs_ticker_history_id',
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id', name='pk_highs'),
        schema='algorithms'
    )

    # Create indexes for highs table
    op.create_index('ix_highs_ticker_history_id', 'highs', ['ticker_history_id'], schema='algorithms')
    op.create_index('ix_highs_threshold', 'highs', ['threshold'], schema='algorithms')
    op.create_index('ix_highs_last_updated', 'highs', ['last_updated'], schema='algorithms')
    op.create_index('ix_highs_expired', 'highs', ['expired'], schema='algorithms')

    # Create reversals table
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
        sa.ForeignKeyConstraint(
            ['ticker_history_id'],
            ['equities.ticker_history.id'],
            name='fk_reversals_ticker_history_id',
            ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id', name='pk_reversals'),
        schema='algorithms'
    )

    # Create indexes for reversals table
    op.create_index('ix_reversals_ticker_history_id', 'reversals', ['ticker_history_id'], schema='algorithms')
    op.create_index('ix_reversals_threshold', 'reversals', ['threshold'], schema='algorithms')
    op.create_index('ix_reversals_high_threshold_date', 'reversals', ['high_threshold_date'], schema='algorithms')
    op.create_index('ix_reversals_reversal_date', 'reversals', ['reversal_date'], schema='algorithms')


def downgrade() -> None:
    """Drop highs and reversals tables."""
    op.drop_table('reversals', schema='algorithms')
    op.drop_table('highs', schema='algorithms')