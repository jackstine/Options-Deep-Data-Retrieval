"""Simple setup test - single test to verify Docker, database, and repository basics.

This test:
1. Creates a PostgreSQL Docker container
2. Sets up the database schema
3. Inserts 1 company using a repository
4. Selects that company from the repository
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

# IMPORTANT: Set environment variables BEFORE importing any src modules
# This prevents CONFIG from initializing during import time
os.environ["OPTIONS_DEEP_ENV"] = "local-test"
os.environ["OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD"] = "test"
os.environ["ENVIRONMENT"] = "local-test"
os.environ["NASDAQ_API_KEY"] = "test_key"
os.environ["EODHD_API_KEY"] = "test_key"

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.postgres import PostgresContainer

from src.database.equities.enums import DataSourceEnum
from src.models.company import Company
# Note: CompanyRepository imported inside test function after port is set


def test_simple_setup():
    """Simple end-to-end test: container -> schema -> insert -> select."""

    print("\n" + "="*80)
    print("STEP 1: Starting PostgreSQL container...")
    print("="*80)

    # Start PostgreSQL container
    with PostgresContainer("postgres:16", username="test", password="test", dbname="test") as postgres:

        # Get connection details
        host = postgres.get_container_host_ip()
        port = postgres.get_exposed_port(5432)
        database = "test"
        username = "test"
        password = "test"

        print(f"✓ Container started: {host}:{port}")
        print(f"  Database: {database}, User: {username}")

        print("\n" + "="*80)
        print("STEP 2: Setting up environment variables...")
        print("="*80)

        # Set environment variables for test
        os.environ["OPTIONS_DEEP_ENV"] = "local-test"
        os.environ["OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD"] = password
        os.environ["OPTIONS_DEEP_TEST_DB_PORT"] = str(port)
        os.environ["ENVIRONMENT"] = "local-test"
        os.environ["NASDAQ_API_KEY"] = "test_key"
        os.environ["EODHD_API_KEY"] = "test_key"

        print(f"✓ OPTIONS_DEEP_ENV = local-test")
        print(f"✓ OPTIONS_DEEP_TEST_DB_PORT = {port}")

        print("\n" + "="*80)
        print("STEP 3: Running Alembic migrations to create schema...")
        print("="*80)

        # Get project root and alembic.ini path
        project_root = Path(__file__).parent.parent.parent
        alembic_ini_path = project_root / "src" / "database" / "equities" / "alembic.ini"

        # Run alembic upgrade head
        env = os.environ.copy()
        result = subprocess.run(
            ["alembic", "-c", str(alembic_ini_path), "upgrade", "head"],
            cwd=str(project_root),
            env=env,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print(f"✗ Alembic migration failed!")
            print(f"STDOUT:\n{result.stdout}")
            print(f"STDERR:\n{result.stderr}")
            raise RuntimeError("Alembic migration failed")

        print("✓ Alembic migrations completed successfully")

        print("\n" + "="*80)
        print("STEP 4: Verifying tables were created...")
        print("="*80)

        # Create direct connection to verify tables
        connection_string = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"
        engine = create_engine(connection_string)

        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public' ORDER BY table_name"
            ))
            tables = [row[0] for row in result]

        print(f"✓ Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table}")

        # Verify companies table exists
        assert "companies" in tables, "companies table should exist"

        print("\n" + "="*80)
        print("STEP 5: Creating repository and inserting company...")
        print("="*80)

        # Now import CompanyRepository after dynamic port is set
        # This ensures CONFIG reads the correct port
        from src.repos.equities.companies.company_repository import CompanyRepository

        # Create repository
        repo = CompanyRepository()
        print(f"✓ Repository created with dynamic port: {port}")

        # Create test company
        test_company = Company(
            company_name="Test Company Inc.",
            exchange="NASDAQ",
            sector="Technology",
            industry="Software",
            country="USA",
            market_cap=1000000000,
            active=True,
            source=DataSourceEnum.EODHD,
        )

        print(f"Inserting company: {test_company.company_name}")

        # Insert company
        inserted = repo.insert(test_company)

        print(f"✓ Company inserted with ID: {inserted.id}")
        assert inserted.id is not None, "Company should have an ID after insert"
        assert inserted.id > 0, "Company ID should be positive"

        company_id = inserted.id

        print("\n" + "="*80)
        print("STEP 6: Selecting company from repository...")
        print("="*80)

        # Select company by ID
        retrieved = repo.get_by_id(company_id)

        print(f"✓ Retrieved company: {retrieved.company_name}")
        assert retrieved is not None, "Should retrieve the company"
        assert retrieved.id == company_id, "IDs should match"
        assert retrieved.company_name == "Test Company Inc.", "Company name should match"
        assert retrieved.exchange == "NASDAQ", "Exchange should match"
        assert retrieved.active is True, "Active status should match"

        print("\n" + "="*80)
        print("✅ ALL STEPS COMPLETED SUCCESSFULLY!")
        print("="*80)
        print("Summary:")
        print("  ✓ Container started")
        print("  ✓ Schema created via Alembic")
        print("  ✓ Company inserted via repository")
        print("  ✓ Company retrieved via repository")
        print("  ✓ All data matched correctly")
        print("="*80)
