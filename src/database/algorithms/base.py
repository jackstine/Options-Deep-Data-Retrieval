"""SQLAlchemy base configuration for Algorithms database."""

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from src.database.config import get_database_config

# Create the declarative base for algorithms tables
Base = declarative_base()


# Database engine and session for algorithms
def get_engine() -> Engine:
    """Get database engine for algorithms database."""
    config = get_database_config("algorithm")
    return create_engine(config.get_connection_string())


def get_session() -> Session:
    """Get database session for algorithms database."""
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def create_tables() -> None:
    """Create all tables in the algorithms database."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
