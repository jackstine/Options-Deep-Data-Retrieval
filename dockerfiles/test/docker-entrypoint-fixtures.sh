#!/bin/bash
# Docker entrypoint script for loading test fixtures
# This script runs during container initialization to seed the database with test data
# Executed after migrations (numbered 20-* to run after 10-run-migrations.sh)

set -e

# Marker file to prevent re-running on container restart
MARKER_FILE="/tmp/fixtures_loaded"

if [ -f "$MARKER_FILE" ]; then
    echo "📦 Test fixtures already loaded, skipping..."
    exit 0
fi

echo "🌱 Loading test fixtures into database..."

cd /opt/options-deep

# Set DOCKER_INIT for Unix socket connection during container initialization
export DOCKER_INIT=true

# Run the Python fixture seeding script
/opt/venv/bin/python /opt/options-deep/dockerfiles/test/data_fill/seed_test_fixtures.py

# Check if seeding was successful
if [ $? -eq 0 ]; then
    echo "✅ Test fixtures loaded successfully"
    # Create marker file to prevent re-running
    touch "$MARKER_FILE"
    exit 0
else
    echo "❌ Failed to load test fixtures"
    exit 1
fi
