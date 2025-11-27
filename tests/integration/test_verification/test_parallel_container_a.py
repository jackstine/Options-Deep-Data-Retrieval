"""Parallel container test A - demonstrates container isolation.

This test creates its own PostgreSQL Docker container and runs independently
from other tests. When run with pytest-xdist (pytest -n 2), this test will
execute in parallel with test_parallel_container_b.py, each with their own
isolated database container.

NOTE: This test uses the options-deep-test:latest Docker image which has
Alembic migrations pre-applied. Build the image first using:
    make build-test-image
"""

from __future__ import annotations

import os
from datetime import datetime

# IMPORTANT: Set environment variables BEFORE importing any src modules
# This prevents CONFIG from initializing during import time
os.environ["OPTIONS_DEEP_ENV"] = "local-test"
os.environ["OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD"] = "test"
os.environ["ENVIRONMENT"] = "local-test"
os.environ["NASDAQ_API_KEY"] = "test_key"
os.environ["EODHD_API_KEY"] = "test_key"

from testcontainers.postgres import PostgresContainer

from src.database.equities.enums import DataSourceEnum
from src.models.company import Company


def test_parallel_container_a():
    """Test A: Creates own container and inserts Company A."""

    start_time = datetime.now()
    print("\n" + "=" * 80)
    print(f"TEST A: Started at {start_time.strftime('%H:%M:%S.%f')[:-3]}")
    print("=" * 80)

    # Start PostgreSQL container with pre-applied migrations
    # This container is INDEPENDENT from any other test containers
    with PostgresContainer(
        "options-deep-test:latest", username="test", password="test", dbname="test"
    ) as postgres:

        # Get connection details
        host = postgres.get_container_host_ip()
        port = postgres.get_exposed_port(5432)

        container_start = datetime.now()
        print(f"\n✓ TEST A: Container started at {container_start.strftime('%H:%M:%S.%f')[:-3]}")
        print(f"  Container: {host}:{port}")
        print(f"  Time elapsed: {(container_start - start_time).total_seconds():.3f}s")

        # Set environment variables for this test's dynamic port
        os.environ["OPTIONS_DEEP_ENV"] = "local-test"
        os.environ["OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD"] = "test"
        os.environ["OPTIONS_DEEP_TEST_DB_PORT"] = str(port)
        os.environ["ENVIRONMENT"] = "local-test"
        os.environ["NASDAQ_API_KEY"] = "test_key"
        os.environ["EODHD_API_KEY"] = "test_key"

        print(f"\n✓ TEST A: Environment configured (port {port})")

        # Import repository AFTER port is set
        from src.repos.equities.companies.company_repository import CompanyRepository

        repo = CompanyRepository()
        repo_ready = datetime.now()
        print(f"✓ TEST A: Repository created at {repo_ready.strftime('%H:%M:%S.%f')[:-3]}")
        print(f"  Time elapsed: {(repo_ready - start_time).total_seconds():.3f}s")

        # Create and insert Company A
        company_a = Company(
            company_name="Parallel Test Company A",
            exchange="NASDAQ",
            sector="Technology",
            industry="Software",
            country="USA",
            market_cap=1500000000,  # 1.5 billion (under INTEGER max of ~2.1B)
            active=True,
            source=DataSourceEnum.EODHD,
        )

        print(f"\n→ TEST A: Inserting company: {company_a.company_name}")

        inserted = repo.insert(company_a)
        insert_time = datetime.now()

        print(f"✓ TEST A: Company inserted at {insert_time.strftime('%H:%M:%S.%f')[:-3]}")
        print(f"  Company ID: {inserted.id}")
        print(f"  Company Name: {inserted.company_name}")
        print(f"  Time elapsed: {(insert_time - start_time).total_seconds():.3f}s")

        # Verify insertion
        assert inserted.id is not None, "Company should have an ID after insert"
        assert inserted.id > 0, "Company ID should be positive"
        assert inserted.company_name == "Parallel Test Company A"

        # Retrieve to verify
        retrieved = repo.get_by_id(inserted.id)
        retrieve_time = datetime.now()

        print(f"\n✓ TEST A: Company retrieved at {retrieve_time.strftime('%H:%M:%S.%f')[:-3]}")
        print(f"  Retrieved: {retrieved.company_name}")
        print(f"  Time elapsed: {(retrieve_time - start_time).total_seconds():.3f}s")

        assert retrieved is not None
        assert retrieved.id == inserted.id
        assert retrieved.company_name == "Parallel Test Company A"

        end_time = datetime.now()
        print("\n" + "=" * 80)
        print(f"✅ TEST A: COMPLETED at {end_time.strftime('%H:%M:%S.%f')[:-3]}")
        print(f"   Total duration: {(end_time - start_time).total_seconds():.3f}s")
        print("=" * 80)

    # Container automatically cleaned up when context exits
    cleanup_time = datetime.now()
    print(f"✓ TEST A: Container cleaned up at {cleanup_time.strftime('%H:%M:%S.%f')[:-3]}")
