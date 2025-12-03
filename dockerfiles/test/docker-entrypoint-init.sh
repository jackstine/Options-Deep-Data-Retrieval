#!/bin/bash
# Docker entrypoint script for creating databases and applying Alembic migrations
# This script runs automatically after PostgreSQL initializes the default database
# Scripts in /docker-entrypoint-initdb.d/ are executed in alphabetical order

set -e  # Exit immediately if a command exits with a non-zero status

echo "========================================================================"
echo "Options Deep: Creating databases and running migrations..."
echo "========================================================================"

# PostgreSQL is already running when this script executes
# No need to wait - scripts in docker-entrypoint-initdb.d run after DB is ready
echo "✓ PostgreSQL is ready (initialization scripts run after server starts)"

# Change to the working directory where alembic.ini is located
cd /opt/options-deep

# Set flag to tell env.py to use Unix socket (not TCP localhost)
# During Docker initialization, PostgreSQL only listens on Unix socket
export DOCKER_INIT=true

# Create algorithm-test database (equities-test already exists from PGDATABASE env var)
echo ""
echo "Creating algorithm-test database..."
psql -U test -d equities-test <<-EOSQL
    CREATE DATABASE "algorithm-test";
EOSQL

if [ $? -eq 0 ]; then
    echo "✓ algorithm-test database created successfully!"
else
    echo "✗ Failed to create algorithm-test database!"
    exit 1
fi

# Run Equities Alembic migrations
echo ""
echo "========================================================================"
echo "Running equities migrations..."
echo "========================================================================"
/opt/venv/bin/alembic -c src/database/equities/alembic.ini upgrade head

# Check if equities migrations succeeded
if [ $? -eq 0 ]; then
    echo "✓ Equities migrations completed successfully!"
    echo ""
    echo "Tables in equities-test database:"
    PGPASSWORD=test psql -U test -d equities-test -c "\dt" | grep "public |" || true
else
    echo "✗ Equities migrations failed!"
    echo "========================================================================"
    exit 1
fi

# Run Algorithms Alembic migrations
echo ""
echo "========================================================================"
echo "Running algorithms migrations..."
echo "========================================================================"
/opt/venv/bin/alembic -c src/database/algorithms/alembic.ini upgrade head

# Check if algorithms migrations succeeded
if [ $? -eq 0 ]; then
    echo "✓ Algorithms migrations completed successfully!"
    echo ""
    echo "Tables in algorithm-test database:"
    PGPASSWORD=test psql -U test -d algorithm-test -c "\dt" | grep "public |" || true
else
    echo "✗ Algorithms migrations failed!"
    echo "========================================================================"
    exit 1
fi

echo ""
echo "========================================================================"
echo "✓ All databases created and migrations completed successfully!"
echo "========================================================================"
