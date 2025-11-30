#!/bin/bash
# Docker entrypoint script for applying Alembic migrations
# This script runs automatically after PostgreSQL initializes the database
# Scripts in /docker-entrypoint-initdb.d/ are executed in alphabetical order

set -e  # Exit immediately if a command exits with a non-zero status

echo "========================================================================"
echo "Options Deep: Running Alembic migrations..."
echo "========================================================================"

# PostgreSQL is already running when this script executes
# No need to wait - scripts in docker-entrypoint-initdb.d run after DB is ready
echo "✓ PostgreSQL is ready (initialization scripts run after server starts)"

# Change to the working directory where alembic.ini is located
cd /opt/options-deep

# Set flag to tell env.py to use Unix socket (not TCP localhost)
# During Docker initialization, PostgreSQL only listens on Unix socket
export DOCKER_INIT=true

# Run Alembic migrations to create all tables
echo "Executing: alembic upgrade head"
/opt/venv/bin/alembic -c src/database/equities/alembic.ini upgrade head

# Check if migrations succeeded
if [ $? -eq 0 ]; then
    echo "✓ Alembic migrations completed successfully!"
    echo ""
    echo "Tables created:"
    # Use psql without -h to connect via Unix socket (default during initialization)
    PGPASSWORD=test psql -U test -d test -c "\dt" | grep "public |" || true
    echo "========================================================================"
else
    echo "✗ Alembic migrations failed!"
    echo "========================================================================"
    exit 1
fi
