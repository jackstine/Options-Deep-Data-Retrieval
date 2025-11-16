"""add_ticker_history_stats_table_and_is_valid_data

Revision ID: a0304e84f829
Revises: f0eadb88da66
Create Date: 2025-11-15 13:45:15.887306

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a0304e84f829'
down_revision: str | Sequence[str] | None = 'f0eadb88da66'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Add is_valid_data column to companies table
    with op.batch_alter_table('companies', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('is_valid_data', sa.Boolean(), nullable=False, server_default='true')
        )
        batch_op.create_index('ix_companies_is_valid_data', ['is_valid_data'])

    # 2. Create ticker_history_stats table
    op.create_table(
        'ticker_history_stats',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('ticker_history_id', sa.Integer(), nullable=False),
        sa.Column('data_coverage_pct', sa.Integer(), nullable=True),
        sa.Column('min_price', sa.BigInteger(), nullable=True),
        sa.Column('max_price', sa.BigInteger(), nullable=True),
        sa.Column('average_price', sa.BigInteger(), nullable=True),
        sa.Column('median_price', sa.BigInteger(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['ticker_history_id'], ['ticker_history.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ticker_history_id', name='uq_ticker_history_stats'),
        comment='Statistical data for ticker histories with prices stored as integers (×1,000,000)'
    )

    # Create index on ticker_history_id
    op.create_index('ix_ticker_history_stats_ticker_history_id', 'ticker_history_stats', ['ticker_history_id'])


def downgrade() -> None:
    """Downgrade schema."""
    # 1. Drop ticker_history_stats table (with index)
    op.drop_index('ix_ticker_history_stats_ticker_history_id', table_name='ticker_history_stats')
    op.drop_table('ticker_history_stats')

    # 2. Remove is_valid_data column from companies table
    with op.batch_alter_table('companies', schema=None) as batch_op:
        batch_op.drop_index('ix_companies_is_valid_data')
        batch_op.drop_column('is_valid_data')
