"""SQLAlchemy base configuration for Equities database."""

from src.config.configuration import CONFIG

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# This is the primary database for this configuration.
DATABASE = "equities"

# Create the declarative base for equities tables
Base = declarative_base()


# Database engine and session for equities
def get_engine():
    """Get database engine for equities database."""
    config = CONFIG.get_database_config(DATABASE)
    return create_engine(config.get_connection_string())


def get_session():
    """Get database session for equities database."""
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def create_tables():
    """Create all tables in the equities database."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
