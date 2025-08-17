"""SQLAlchemy base configuration."""

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from src.config.configuration import CONFIG

# Create the declarative base
Base = declarative_base()


# Database engine and session
def get_engine(database_name: str = "equities") -> Engine:
    """Get database engine for current environment and database."""
    config = CONFIG.get_database_config(database_name)
    return create_engine(config.get_connection_string())


def get_session(database_name: str = "equities") -> Session:
    """Get database session for current environment and database."""
    engine = get_engine(database_name)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def create_tables(database_name: str = "equities") -> None:
    """Create all tables in the specified database."""
    engine = get_engine(database_name)
    Base.metadata.create_all(bind=engine)
