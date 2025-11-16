"""add_ticker_history_id_to_ticker_and_rename_in_pricing

Revision ID: 99915edd52d4
Revises: a0304e84f829
Create Date: 2025-11-16 09:52:56.686007

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '99915edd52d4'
down_revision: Union[str, Sequence[str], None] = 'a0304e84f829'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    1. Add ticker_history_id column to ticker table with foreign key
    2. Rename ticker_id to ticker_history_id in historical_eod_pricing table
    3. Update primary key constraint in historical_eod_pricing
    """
    # 1. Add ticker_history_id column to ticker table
    # Note: Since this is a new column with NOT NULL constraint, we need to handle existing data
    # For now, we'll make it nullable first, then add NOT NULL constraint after data migration
    with op.batch_alter_table('tickers', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('ticker_history_id', sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            'fk_tickers_ticker_history_id',
            'ticker_history',
            ['ticker_history_id'],
            ['id']
        )
        batch_op.create_index('ix_tickers_ticker_history_id', ['ticker_history_id'])

    # 2. Rename ticker_id to ticker_history_id in historical_eod_pricing
    # First, drop the old primary key constraint
    with op.batch_alter_table('historical_eod_pricing', schema=None) as batch_op:
        batch_op.drop_constraint('pk_ticker_date', type_='primary')
        batch_op.alter_column('ticker_id', new_column_name='ticker_history_id')
        # Create new primary key with the renamed column
        batch_op.create_primary_key(
            'pk_ticker_history_date',
            ['ticker_history_id', 'date']
        )


def downgrade() -> None:
    """Downgrade schema.

    1. Rename ticker_history_id back to ticker_id in historical_eod_pricing
    2. Remove ticker_history_id column from ticker table
    """
    # 1. Rename ticker_history_id back to ticker_id in historical_eod_pricing
    with op.batch_alter_table('historical_eod_pricing', schema=None) as batch_op:
        batch_op.drop_constraint('pk_ticker_history_date', type_='primary')
        batch_op.alter_column('ticker_history_id', new_column_name='ticker_id')
        batch_op.create_primary_key('pk_ticker_date', ['ticker_id', 'date'])

    # 2. Remove ticker_history_id from ticker table
    with op.batch_alter_table('tickers', schema=None) as batch_op:
        batch_op.drop_index('ix_tickers_ticker_history_id')
        batch_op.drop_constraint('fk_tickers_ticker_history_id', type_='foreignkey')
        batch_op.drop_column('ticker_history_id')
