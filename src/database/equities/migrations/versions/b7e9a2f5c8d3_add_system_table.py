"""add_system_table

Revision ID: b7e9a2f5c8d3
Revises: adb6f111d132
Create Date: 2025-11-25 21:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7e9a2f5c8d3'
down_revision: Union[str, Sequence[str], None] = 'adb6f111d132'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create system table
    op.create_table(
        "system",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("system_name", sa.Integer(), nullable=False),
        sa.Column("key", sa.Integer(), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("system_name", "key", name="uq_system_name_key"),
        comment="System configuration key-value store with integer keys",
    )

    # Create indexes
    op.create_index(
        op.f("ix_system_system_name"),
        "system",
        ["system_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_system_key"),
        "system",
        ["key"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop indexes
    op.drop_index(op.f("ix_system_key"), table_name="system")
    op.drop_index(op.f("ix_system_system_name"), table_name="system")

    # Drop table
    op.drop_table("system")
