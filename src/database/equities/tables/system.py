"""SQLAlchemy System table for database operations."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.database.equities.base import Base


class System(Base):
    """SQLAlchemy model for system configuration data.

    Key-value store for system-level configuration organized by system_name.
    Both system_name and key are integers for efficient lookups.
    """

    __tablename__ = "system"

    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # System name identifier
    system_name: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Configuration key identifier
    key: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Configuration value (stored as text, parsed by application layer)
    value: Mapped[str] = mapped_column(Text, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("system_name", "key", name="uq_system_name_key"),
        {"comment": "System configuration key-value store with integer keys"},
    )

    def __repr__(self) -> str:
        """String representation of System."""
        return f"<System(system_name={self.system_name}, key={self.key}, value={self.value[:50]})>"
