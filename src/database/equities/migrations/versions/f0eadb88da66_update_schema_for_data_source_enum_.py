"""Update schema for data source enum, remove ticker_history active, update historical_eod_pricing FK and PK

Revision ID: f0eadb88da66
Revises: ebbbc3162c18
Create Date: 2025-11-15 12:02:37.560065

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f0eadb88da66'
down_revision: str | Sequence[str] | None = 'ebbbc3162c18'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create enum type for data sources
    data_source_enum = sa.Enum('EODHD', name='data_source_enum')
    data_source_enum.create(op.get_bind())

    # 1. Update companies table - change source from string to enum
    with op.batch_alter_table('companies', schema=None) as batch_op:
        # Since database is empty, we can directly alter the column type
        batch_op.alter_column('source',
                            existing_type=sa.String(50),
                            type_=data_source_enum,
                            existing_nullable=False,
                            postgresql_using='source::data_source_enum')

    # 2. Remove active field from ticker_history
    with op.batch_alter_table('ticker_history', schema=None) as batch_op:
        batch_op.drop_index('ix_ticker_history_active', if_exists=True)
        batch_op.drop_column('active')

    # 3. Update historical_eod_pricing table
    with op.batch_alter_table('historical_eod_pricing', schema=None) as batch_op:
        # Drop the existing unique constraint
        batch_op.drop_constraint('uq_ticker_date', type_='unique')

        # Drop foreign key to tickers.id
        batch_op.drop_constraint('historical_eod_pricing_ticker_id_fkey', type_='foreignkey')

        # Drop the id primary key column
        batch_op.drop_column('id')

        # Add foreign key to ticker_history.id
        batch_op.create_foreign_key(
            'historical_eod_pricing_ticker_id_fkey',
            'ticker_history',
            ['ticker_id'],
            ['id'],
            ondelete='CASCADE'
        )

        # Add composite primary key
        batch_op.create_primary_key('pk_ticker_date', ['ticker_id', 'date'])


def downgrade() -> None:
    """Downgrade schema."""
    # 1. Revert historical_eod_pricing table changes
    with op.batch_alter_table('historical_eod_pricing', schema=None) as batch_op:
        # Drop composite primary key
        batch_op.drop_constraint('pk_ticker_date', type_='primary')

        # Drop foreign key to ticker_history.id
        batch_op.drop_constraint('historical_eod_pricing_ticker_id_fkey', type_='foreignkey')

        # Add back id column as primary key
        batch_op.add_column(sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, primary_key=True))

        # Add back foreign key to tickers.id
        batch_op.create_foreign_key(
            'historical_eod_pricing_ticker_id_fkey',
            'tickers',
            ['ticker_id'],
            ['id'],
            ondelete='CASCADE'
        )

        # Add back unique constraint
        batch_op.create_unique_constraint('uq_ticker_date', ['ticker_id', 'date'])

    # 2. Add back active field to ticker_history
    with op.batch_alter_table('ticker_history', schema=None) as batch_op:
        batch_op.add_column(sa.Column('active', sa.Boolean(), nullable=False, server_default='true'))
        batch_op.create_index('ix_ticker_history_active', ['active'])

    # 3. Revert companies table - change source from enum to string
    with op.batch_alter_table('companies', schema=None) as batch_op:
        batch_op.alter_column('source',
                            existing_type=sa.Enum('EODHD', name='data_source_enum'),
                            type_=sa.String(50),
                            existing_nullable=False,
                            postgresql_using='source::text')

    # Drop enum type
    sa.Enum(name='data_source_enum').drop(op.get_bind())
