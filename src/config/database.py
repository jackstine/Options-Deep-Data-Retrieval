"""Database configuration for multiple environments."""

from __future__ import annotations
import os
import json
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv


@dataclass
class DatabaseConfig:
    """Database configuration class."""
    
    host: str
    port: int
    database: str
    username: str
    password: str
    environment: str
    
    def get_connection_string(self) -> str:
        """
        Get PostgreSQL connection string.
        
        Returns:
            SQLAlchemy connection string
        """
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    def get_async_connection_string(self) -> str:
        """
        Get PostgreSQL async connection string.
        
        Returns:
            SQLAlchemy async connection string
        """
        return f"postgresql+asyncpg://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


class DatabaseEnvironment:
    """Database environment configuration manager."""
    
    def __init__(self) -> None:
        """Initialize database environment."""
        load_dotenv()
        self._environment = os.getenv('ENVIRONMENT', 'local').lower()
        self._config_dir = Path(__file__).parent / 'environment_configs'
    
    def get_config(self) -> DatabaseConfig:
        """
        Get database configuration for current environment.
        
        Returns:
            DatabaseConfig for the current environment
            
        Raises:
            ValueError: If environment is not supported or configuration is missing
        """
        config_file = self._config_dir / f"{self._environment}.json"
        
        if not config_file.exists():
            raise ValueError(f"Database config file not found: {config_file}")
        
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            # Get password from environment variable
            password = os.getenv('OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD')
            
            if password is None:
                raise ValueError("Database password environment variable OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD is not set")
            
            return DatabaseConfig(
                host=config_data['host'],
                port=config_data['port'],
                database=config_data['database'],
                username=config_data['username'],
                password=password,
                environment=self._environment
            )
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file {config_file}: {e}")
        except KeyError as e:
            raise ValueError(f"Missing required field in config file {config_file}: {e}")
    
    @property
    def environment(self) -> str:
        """Get current environment name."""
        return self._environment


# Global instance
DATABASE_ENV = DatabaseEnvironment()