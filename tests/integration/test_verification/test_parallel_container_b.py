"""Parallel container test B - demonstrates container isolation.

This test creates its own PostgreSQL Docker container and runs independently
from other tests. When run with pytest-xdist (pytest -n 2), this test will
execute in parallel with test_parallel_container_a.py, each with their own
isolated database container.

NOTE: This test uses the options-deep-test:latest Docker image which has
Alembic migrations pre-applied. Build the image first using:
    make build-test-image
"""

from __future__ import annotations

from datetime import datetime

# IMPORTANT: Set environment variables BEFORE importing any src modules
from tests.integration.common_setup import setup_test_environment

setup_test_environment()

from src.database.equities.enums import DataSourceEnum
from src.models.company import Company
from tests.integration.common_setup import integration_test_container


def test_parallel_container_b():
    """Test B: Creates own container and inserts Company B."""

    start_time = datetime.now()
    print("\n" + "=" * 80)
    print(f"TEST B: Started at {start_time.strftime('%H:%M:%S.%f')[:-3]}")
    print("=" * 80)

    # Start PostgreSQL container using common setup
    with integration_test_container() as (postgres, repo, port):

        # Get connection details
        host = postgres.get_container_host_ip()

        container_start = datetime.now()
        print(f"\n✓ TEST B: Container started at {container_start.strftime('%H:%M:%S.%f')[:-3]}")
        print(f"  Container: {host}:{port}")
        print(f"  Time elapsed: {(container_start - start_time).total_seconds():.3f}s")

        print(f"\n✓ TEST B: Environment configured (port {port})")

        repo_ready = datetime.now()
        print(f"✓ TEST B: Repository created at {repo_ready.strftime('%H:%M:%S.%f')[:-3]}")
        print(f"  Time elapsed: {(repo_ready - start_time).total_seconds():.3f}s")

        # Create and insert Company B
        company_b = Company(
            company_name="Parallel Test Company B",
            exchange="NYSE",
            sector="Finance",
            industry="Banking",
            country="USA",
            market_cap=1800000000,  # 1.8 billion (under INTEGER max of ~2.1B)
            active=True,
            source=DataSourceEnum.EODHD,
        )

        print(f"\n→ TEST B: Inserting company: {company_b.company_name}")

        inserted = repo.insert(company_b)
        insert_time = datetime.now()

        print(f"✓ TEST B: Company inserted at {insert_time.strftime('%H:%M:%S.%f')[:-3]}")
        print(f"  Company ID: {inserted.id}")
        print(f"  Company Name: {inserted.company_name}")
        print(f"  Time elapsed: {(insert_time - start_time).total_seconds():.3f}s")

        # Verify insertion
        assert inserted.id is not None, "Company should have an ID after insert"
        assert inserted.id > 0, "Company ID should be positive"
        assert inserted.company_name == "Parallel Test Company B"

        # Retrieve to verify
        retrieved = repo.get_by_id(inserted.id)
        retrieve_time = datetime.now()

        print(f"\n✓ TEST B: Company retrieved at {retrieve_time.strftime('%H:%M:%S.%f')[:-3]}")
        print(f"  Retrieved: {retrieved.company_name}")
        print(f"  Time elapsed: {(retrieve_time - start_time).total_seconds():.3f}s")

        assert retrieved is not None
        assert retrieved.id == inserted.id
        assert retrieved.company_name == "Parallel Test Company B"

        end_time = datetime.now()
        print("\n" + "=" * 80)
        print(f"✅ TEST B: COMPLETED at {end_time.strftime('%H:%M:%S.%f')[:-3]}")
        print(f"   Total duration: {(end_time - start_time).total_seconds():.3f}s")
        print("=" * 80)

    # Container automatically cleaned up when context exits
    cleanup_time = datetime.now()
    print(f"✓ TEST B: Container cleaned up at {cleanup_time.strftime('%H:%M:%S.%f')[:-3]}")
