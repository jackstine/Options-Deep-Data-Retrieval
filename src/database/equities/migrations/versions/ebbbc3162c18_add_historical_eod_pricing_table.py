"""add_historical_eod_pricing_table

Revision ID: ebbbc3162c18
Revises: 908a36c712dc
Create Date: 2025-11-08 21:36:22.372231

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ebbbc3162c18'
down_revision: Union[str, Sequence[str], None] = '908a36c712dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create historical_eod_pricing table
    op.create_table(
        "historical_eod_pricing",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ticker_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("open", sa.BigInteger(), nullable=False),
        sa.Column("high", sa.BigInteger(), nullable=False),
        sa.Column("low", sa.BigInteger(), nullable=False),
        sa.Column("close", sa.BigInteger(), nullable=False),
        sa.Column("adjusted_close", sa.BigInteger(), nullable=False),
        sa.Column("volume", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["ticker_id"],
            ["tickers.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticker_id", "date", name="uq_ticker_date"),
        comment="Historical end-of-day pricing data with prices stored as integers (×10,000)",
    )

    # Create indexes
    op.create_index(
        op.f("ix_historical_eod_pricing_ticker_id"),
        "historical_eod_pricing",
        ["ticker_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_historical_eod_pricing_date"),
        "historical_eod_pricing",
        ["date"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index(
        op.f("ix_historical_eod_pricing_date"), table_name="historical_eod_pricing"
    )
    op.drop_index(
        op.f("ix_historical_eod_pricing_ticker_id"),
        table_name="historical_eod_pricing",
    )

    # Drop table
    op.drop_table("historical_eod_pricing")
