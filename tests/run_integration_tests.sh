#!/bin/bash
# Integration test runner script
# This script sets up the environment and runs integration tests with testcontainers
# Features:
# - Smart migration detection: automatically rebuilds both test and test-data Docker images if migrations changed
# - Parallel execution: runs tests in parallel using all CPU cores by default
# - Proper environment setup: sets all required variables including TESTCONTAINERS_RYUK_DISABLED

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Options Deep Integration Test Runner ===${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}ERROR: Docker is not running!${NC}"
    echo "Please start Docker Desktop and try again."
    exit 1
fi

echo -e "${GREEN}✓ Docker is running${NC}"

# Get script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT"

# Smart migration detection: check if Docker image needs rebuild
echo -e "${BLUE}🔍 Checking if test Docker image needs rebuild...${NC}"

IMAGE_NAME="options-deep-test:latest"
NEEDS_REBUILD=false

# Check if image exists
if ! docker image inspect "$IMAGE_NAME" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Docker image '$IMAGE_NAME' not found${NC}"
    NEEDS_REBUILD=true
else
    # Get image creation timestamp (Unix timestamp)
    IMAGE_CREATED=$(docker image inspect "$IMAGE_NAME" --format='{{.Created}}' 2>/dev/null)
    IMAGE_TIMESTAMP=$(date -j -f "%Y-%m-%dT%H:%M:%S" "$(echo "$IMAGE_CREATED" | cut -d'.' -f1)" "+%s" 2>/dev/null || echo "0")

    # Find newest migration file in equities migrations
    MIGRATIONS_DIR="src/database/equities/migrations/versions"
    if [ -d "$MIGRATIONS_DIR" ]; then
        # Find the newest migration file (by modification time)
        NEWEST_MIGRATION=$(find "$MIGRATIONS_DIR" -name "*.py" -type f -exec stat -f "%m %N" {} \; 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)

        if [ -n "$NEWEST_MIGRATION" ]; then
            MIGRATION_TIMESTAMP=$(stat -f "%m" "$NEWEST_MIGRATION" 2>/dev/null || echo "0")

            # Compare timestamps
            if [ "$MIGRATION_TIMESTAMP" -gt "$IMAGE_TIMESTAMP" ]; then
                MIGRATION_FILE=$(basename "$NEWEST_MIGRATION")
                echo -e "${YELLOW}⚠ Migration file '$MIGRATION_FILE' is newer than Docker image${NC}"
                NEEDS_REBUILD=true
            fi
        fi
    fi
fi

# Rebuild image if needed
if [ "$NEEDS_REBUILD" = true ]; then
    echo -e "${BLUE}🔨 Rebuilding test Docker image (migrations changed)...${NC}"
    echo ""

    # Call make build-test-image
    if ! make build-test-image; then
        echo -e "${RED}ERROR: Failed to build test Docker image!${NC}"
        exit 1
    fi

    echo ""
    echo -e "${GREEN}✓ Test Docker image rebuilt successfully${NC}"
else
    echo -e "${GREEN}✓ Test Docker image is up-to-date (no rebuild needed)${NC}"
fi

echo ""

# Smart migration detection: check if test data image needs rebuild
echo -e "${BLUE}🔍 Checking if test data Docker image needs rebuild...${NC}"

DATA_IMAGE_NAME="options-deep-test-data:latest"
DATA_NEEDS_REBUILD=false

# Check if data image exists
if ! docker image inspect "$DATA_IMAGE_NAME" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Docker image '$DATA_IMAGE_NAME' not found${NC}"
    DATA_NEEDS_REBUILD=true
else
    # Get image creation timestamp (Unix timestamp)
    DATA_IMAGE_CREATED=$(docker image inspect "$DATA_IMAGE_NAME" --format='{{.Created}}' 2>/dev/null)
    DATA_IMAGE_TIMESTAMP=$(date -j -f "%Y-%m-%dT%H:%M:%S" "$(echo "$DATA_IMAGE_CREATED" | cut -d'.' -f1)" "+%s" 2>/dev/null || echo "0")

    # Find newest migration file in equities migrations
    MIGRATIONS_DIR="src/database/equities/migrations/versions"
    if [ -d "$MIGRATIONS_DIR" ]; then
        # Find the newest migration file (by modification time)
        NEWEST_MIGRATION=$(find "$MIGRATIONS_DIR" -name "*.py" -type f -exec stat -f "%m %N" {} \; 2>/dev/null | sort -rn | head -1 | cut -d' ' -f2-)

        if [ -n "$NEWEST_MIGRATION" ]; then
            MIGRATION_TIMESTAMP=$(stat -f "%m" "$NEWEST_MIGRATION" 2>/dev/null || echo "0")

            # Compare timestamps
            if [ "$MIGRATION_TIMESTAMP" -gt "$DATA_IMAGE_TIMESTAMP" ]; then
                MIGRATION_FILE=$(basename "$NEWEST_MIGRATION")
                echo -e "${YELLOW}⚠ Migration file '$MIGRATION_FILE' is newer than Docker data image${NC}"
                DATA_NEEDS_REBUILD=true
            fi
        fi
    fi
fi

# Rebuild data image if needed
if [ "$DATA_NEEDS_REBUILD" = true ]; then
    echo -e "${BLUE}🔨 Rebuilding test data Docker image (migrations changed)...${NC}"
    echo ""

    # Call make build-test-data-image
    if ! make build-test-data-image; then
        echo -e "${RED}ERROR: Failed to build test data Docker image!${NC}"
        exit 1
    fi

    echo ""
    echo -e "${GREEN}✓ Test data Docker image rebuilt successfully${NC}"
else
    echo -e "${GREEN}✓ Test data Docker image is up-to-date (no rebuild needed)${NC}"
fi

echo ""

# Set environment variables for tests
export OPTIONS_DEEP_ENV="local-test"
export OPTIONS_DEEP_DATA_WAREHOUSE_PASSWORD="test"
export NASDAQ_API_KEY="test_nasdaq_key"
export EODHD_API_KEY="test_eodhd_key"
export ENVIRONMENT="local-test"
export TESTCONTAINERS_RYUK_DISABLED=true  # Required for parallel test execution

echo -e "${GREEN}✓ Environment variables set${NC}"
echo ""

# Detect number of CPU cores for parallel execution
NUM_CORES=$(sysctl -n hw.ncpu 2>/dev/null || echo "4")

echo -e "${BLUE}🧪 Running integration tests (parallel: $NUM_CORES workers)...${NC}"
echo -e "${BLUE}   Pass custom pytest args to override defaults (e.g., -n 0 for sequential)${NC}"
echo ""

# Run pytest with integration tests
# -n auto: parallel execution using all CPU cores
# -v: verbose output
# -s: show print statements
# --tb=short: shorter traceback format
# --color=yes: colored output
# "$@": pass any additional arguments from command line (allows overriding defaults)
uv run pytest tests/integration/ \
    -n auto \
    -v \
    -s \
    --tb=short \
    --color=yes \
    "$@"

TEST_EXIT_CODE=$?

echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}=== ✓ All integration tests passed! ===${NC}"
else
    echo -e "${RED}=== ✗ Some integration tests failed ===${NC}"
fi

exit $TEST_EXIT_CODE
