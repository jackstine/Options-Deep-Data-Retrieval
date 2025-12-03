#!/bin/bash
# Build Docker test data image with pre-populated fixtures
# This script builds the options-deep-test-data:latest image used for backfill pipeline integration testing

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

DATA_IMAGE_NAME="options-deep-test-data:latest"
BASE_IMAGE_NAME="options-deep-test:latest"

echo -e "${GREEN}========================================================================"
echo -e "Options Deep: Building Test Data Docker Image (with Fixtures)"
echo -e "========================================================================${NC}"
echo ""

# Check if Docker is running
echo -e "${BLUE}Checking Docker status...${NC}"
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}ERROR: Docker is not running!${NC}"
    echo "Please start Docker Desktop and try again."
    exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"
echo ""

# Get script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root for docker build context
cd "$PROJECT_ROOT"

# Check if base image exists (options-deep-test:latest)
if docker images | grep -q "^options-deep-test.*latest"; then
    echo -e "${GREEN}✓ Found base image: ${BASE_IMAGE_NAME}${NC}"
else
    echo -e "${RED}ERROR: Base image '${BASE_IMAGE_NAME}' not found!${NC}"
    echo -e "${YELLOW}Please build the base test image first:${NC}"
    echo -e "${BLUE}  make build-test-image${NC}"
    exit 1
fi
echo ""

# Build data image (layers on top of options-deep-test:latest)
echo -e "${BLUE}Building data image: ${DATA_IMAGE_NAME}${NC}"
echo -e "${BLUE}This image includes:${NC}"
echo -e "${BLUE}  - Schema from ${BASE_IMAGE_NAME}${NC}"
echo -e "${BLUE}  - Pre-populated test fixtures (TESTSPLIT, TESTDELIST, TESTACTIVE)${NC}"
echo ""

docker build -t ${DATA_IMAGE_NAME} -f dockerfiles/test/Dockerfile.data .

BUILD_EXIT_CODE=$?

echo ""

# Verify image was created
if [ $BUILD_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}========================================================================${NC}"
    echo -e "${GREEN}✓ Image built successfully!${NC}"
    echo -e "${GREEN}========================================================================${NC}"
    echo ""
    echo -e "${BLUE}Image details:${NC}"
    docker images | head -1  # Header
    docker images | grep "options-deep-test"
    echo ""
    echo -e "${GREEN}You can now run backfill pipeline integration tests with:${NC}"
    echo -e "${BLUE}  TESTCONTAINERS_RYUK_DISABLED=true uv run pytest tests/integration/algorithms/ -n 2 -v${NC}"
    echo ""
    echo -e "${BLUE}Fixture data included:${NC}"
    echo -e "  - TESTSPLIT:   30 days pricing + 2:1 split on day 15"
    echo -e "  - TESTDELIST:  25 days pricing (delisted company)"
    echo -e "  - TESTACTIVE:  30 days pricing (no splits)"
else
    echo -e "${RED}========================================================================${NC}"
    echo -e "${RED}✗ Image build failed!${NC}"
    echo -e "${RED}========================================================================${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}Build complete!${NC}"
