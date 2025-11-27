"""SQLAlchemy base configuration for Equities database."""

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from src.database.config import get_database_config

# This is the primary database for this configuration.
DATABASE = "equities"

# Create the declarative base for equities tables
Base = declarative_base()


# Database engine and session for equities
def get_engine() -> Engine:
    """Get database engine for equities database."""
    config = get_database_config(DATABASE)
    return create_engine(config.get_connection_string())


def get_session() -> Session:
    """Get database session for equities database."""
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def create_tables() -> None:
    """Create all tables in the equities database."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
