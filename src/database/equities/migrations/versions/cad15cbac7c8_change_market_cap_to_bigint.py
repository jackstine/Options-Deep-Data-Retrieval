"""change_market_cap_to_bigint

Revision ID: cad15cbac7c8
Revises: 350138186251
Create Date: 2025-11-27 17:35:23.580098

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cad15cbac7c8'
down_revision: Union[str, Sequence[str], None] = '350138186251'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Change market_cap column from Integer to BigInteger.

    This is necessary to support large market cap values (trillions)
    that exceed the INTEGER type limit of ~2.1 billion.
    """
    op.alter_column(
        'companies',
        'market_cap',
        type_=sa.BigInteger(),
        existing_type=sa.Integer(),
        nullable=True
    )


def downgrade() -> None:
    """Revert market_cap column from BigInteger to Integer.

    WARNING: This may cause data loss if any market_cap values
    exceed INTEGER limit (2,147,483,647).
    """
    op.alter_column(
        'companies',
        'market_cap',
        type_=sa.Integer(),
        existing_type=sa.BigInteger(),
        nullable=True
    )
