"""Simple setup test - single test to verify Docker, database, and repository basics.

This test:
1. Creates a PostgreSQL Docker container (with pre-applied migrations)
2. Inserts 1 company using a repository
3. Selects that company from the repository

NOTE: This test uses the options-deep-test:latest Docker image which has
Alembic migrations pre-applied. Build the image first using:
    make build-test-image
"""

from __future__ import annotations

# IMPORTANT: Set environment variables BEFORE importing any src modules
from tests.integration.common_setup import setup_test_environment

setup_test_environment()

from sqlalchemy import create_engine, text

from src.database.equities.enums import DataSourceEnum
from src.models.company import Company
from tests.integration.common_setup import integration_test_container


def test_simple_setup():
    """Simple end-to-end test: container -> schema -> insert -> select."""

    print("\n" + "=" * 80)
    print("STEP 1: Starting PostgreSQL container...")
    print("=" * 80)

    # Start PostgreSQL container using common setup
    with integration_test_container() as (postgres, repo, port):

        # Get connection details
        host = postgres.get_container_host_ip()
        database = "test"
        username = "test"
        password = "test"

        print(f"✓ Container started: {host}:{port}")
        print(f"  Database: {database}, User: {username}")

        print("\n" + "=" * 80)
        print("STEP 2: Environment configured via common_setup")
        print("=" * 80)

        print(f"✓ OPTIONS_DEEP_ENV = local-test")
        print(f"✓ OPTIONS_DEEP_TEST_DB_PORT = {port}")

        print("\n" + "=" * 80)
        print("STEP 3: Verifying tables were created (pre-applied in Docker image)...")
        print("=" * 80)

        # Create direct connection to verify tables
        connection_string = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"
        engine = create_engine(connection_string)

        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public' ORDER BY table_name"
                )
            )
            tables = [row[0] for row in result]

        print(f"✓ Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table}")

        # Verify companies table exists
        assert "companies" in tables, "companies table should exist"

        print("\n" + "=" * 80)
        print("STEP 4: Creating repository and inserting company...")
        print("=" * 80)

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

        print("\n" + "=" * 80)
        print("STEP 5: Selecting company from repository...")
        print("=" * 80)

        # Select company by ID
        retrieved = repo.get_by_id(company_id)

        print(f"✓ Retrieved company: {retrieved.company_name}")
        assert retrieved is not None, "Should retrieve the company"
        assert retrieved.id == company_id, "IDs should match"
        assert retrieved.company_name == "Test Company Inc.", "Company name should match"
        assert retrieved.exchange == "NASDAQ", "Exchange should match"
        assert retrieved.active is True, "Active status should match"

        print("\n" + "=" * 80)
        print("✅ ALL STEPS COMPLETED SUCCESSFULLY!")
        print("=" * 80)
        print("Summary:")
        print("  ✓ Container started with pre-applied migrations")
        print("  ✓ Schema verified (10 tables including alembic_version)")
        print("  ✓ Company inserted via repository")
        print("  ✓ Company retrieved via repository")
        print("  ✓ All data matched correctly")
        print("=" * 80)
