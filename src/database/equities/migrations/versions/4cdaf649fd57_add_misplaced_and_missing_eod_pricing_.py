"""add_misplaced_and_missing_eod_pricing_tables

Revision ID: 4cdaf649fd57
Revises: 99915edd52d4
Create Date: 2025-11-16 19:48:29.891458

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '4cdaf649fd57'
down_revision: Union[str, Sequence[str], None] = '99915edd52d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create misplaced_eod_pricing table
    op.create_table(
        'misplaced_eod_pricing',
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('open', sa.BigInteger(), nullable=False),
        sa.Column('high', sa.BigInteger(), nullable=False),
        sa.Column('low', sa.BigInteger(), nullable=False),
        sa.Column('close', sa.BigInteger(), nullable=False),
        sa.Column('adjusted_close', sa.BigInteger(), nullable=False),
        sa.Column('volume', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('symbol', 'date', name='pk_misplaced_symbol_date'),
        comment='Misplaced EOD pricing data without ticker_history associations (prices stored as integers ×1,000,000)'
    )
    # Create indexes for misplaced_eod_pricing
    op.create_index(op.f('ix_misplaced_eod_pricing_symbol'), 'misplaced_eod_pricing', ['symbol'], unique=False)
    op.create_index(op.f('ix_misplaced_eod_pricing_date'), 'misplaced_eod_pricing', ['date'], unique=False)

    # Create missing_eod_pricing table
    op.create_table(
        'missing_eod_pricing',
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('ticker_history_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['ticker_history_id'], ['ticker_history.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('company_id', 'ticker_history_id', 'date', name='pk_missing_pricing_composite'),
        comment='Tracks missing end-of-day pricing data for tickers'
    )
    # Create indexes for missing_eod_pricing
    op.create_index(op.f('ix_missing_eod_pricing_company_id'), 'missing_eod_pricing', ['company_id'], unique=False)
    op.create_index(op.f('ix_missing_eod_pricing_ticker_history_id'), 'missing_eod_pricing', ['ticker_history_id'], unique=False)
    op.create_index(op.f('ix_missing_eod_pricing_date'), 'missing_eod_pricing', ['date'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes for missing_eod_pricing
    op.drop_index(op.f('ix_missing_eod_pricing_date'), table_name='missing_eod_pricing')
    op.drop_index(op.f('ix_missing_eod_pricing_ticker_history_id'), table_name='missing_eod_pricing')
    op.drop_index(op.f('ix_missing_eod_pricing_company_id'), table_name='missing_eod_pricing')
    # Drop missing_eod_pricing table
    op.drop_table('missing_eod_pricing')

    # Drop indexes for misplaced_eod_pricing
    op.drop_index(op.f('ix_misplaced_eod_pricing_date'), table_name='misplaced_eod_pricing')
    op.drop_index(op.f('ix_misplaced_eod_pricing_symbol'), table_name='misplaced_eod_pricing')
    # Drop misplaced_eod_pricing table
    op.drop_table('misplaced_eod_pricing')
