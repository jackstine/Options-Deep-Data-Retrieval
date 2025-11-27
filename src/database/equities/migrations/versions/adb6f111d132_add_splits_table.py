"""add_splits_table

Revision ID: adb6f111d132
Revises: c3d850674719
Create Date: 2025-11-23 18:56:29.598927

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'adb6f111d132'
down_revision: str | Sequence[str] | None = 'c3d850674719'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create splits table
    op.create_table(
        "splits",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("ticker_history_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("split_ratio", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(
            ["ticker_history_id"],
            ["ticker_history.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ticker_history_id", "date", name="uq_splits_ticker_history_date"),
        comment="Stock split data with split ratios stored as strings (e.g., '2.000000/1.000000')",
    )

    # Create indexes
    op.create_index(
        op.f("ix_splits_ticker_history_id"),
        "splits",
        ["ticker_history_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_splits_date"),
        "splits",
        ["date"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index(op.f("ix_splits_date"), table_name="splits")
    op.drop_index(op.f("ix_splits_ticker_history_id"), table_name="splits")

    # Drop table
    op.drop_table("splits")
