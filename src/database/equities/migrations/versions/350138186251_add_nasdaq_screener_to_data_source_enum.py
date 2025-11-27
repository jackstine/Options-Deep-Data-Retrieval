"""add_nasdaq_screener_to_data_source_enum

Revision ID: 350138186251
Revises: b7e9a2f5c8d3
Create Date: 2025-11-27 16:51:29.972470

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '350138186251'
down_revision: Union[str, Sequence[str], None] = 'b7e9a2f5c8d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add NASDAQ_SCREENER value to data_source_enum."""
    # PostgreSQL requires ALTER TYPE to add enum values
    # This must be done outside a transaction block
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE data_source_enum ADD VALUE IF NOT EXISTS 'NASDAQ_SCREENER'")


def downgrade() -> None:
    """Remove NASDAQ_SCREENER value from data_source_enum.

    Note: PostgreSQL does not support removing enum values directly.
    This would require recreating the enum type, which is complex and risky.
    For safety, we're leaving the enum value in place on downgrade.
    """
    # Cannot easily remove enum values in PostgreSQL
    # Would require:
    # 1. Creating a new enum type without the value
    # 2. Converting all columns using the old enum to the new enum
    # 3. Dropping the old enum type
    # 4. Renaming the new enum type
    #
    # This is complex and rarely needed, so we skip it for safety.
    pass
