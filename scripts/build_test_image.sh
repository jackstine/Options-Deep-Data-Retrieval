#!/bin/bash
# Build Docker test image with pre-applied Alembic migrations
# This script builds the options-deep-test:latest image used for integration testing

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

IMAGE_NAME="options-deep-test:latest"
BASE_IMAGE_NAME="options-deep-test-base:latest"

echo -e "${GREEN}========================================================================"
echo -e "Options Deep: Building Test Docker Image (Multi-Stage)"
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

# Check if base image exists
if docker images | grep -q "^options-deep-test-base.*latest"; then
    echo -e "${GREEN}✓ Found existing base image (dependencies cached)${NC}"
    echo -e "${BLUE}Building only migration layer...${NC}"
else
    echo -e "${YELLOW}Base image not found - building from scratch${NC}"
    echo -e "${BLUE}This will take longer (installing Python dependencies)...${NC}"
    echo ""

    # Build base image first
    echo -e "${BLUE}Step 1/2: Building base image with dependencies...${NC}"
    docker build --target base -t ${BASE_IMAGE_NAME} -f dockerfiles/test/Dockerfile .

    BASE_BUILD_EXIT_CODE=$?
    if [ $BASE_BUILD_EXIT_CODE -ne 0 ]; then
        echo -e "${RED}✗ Base image build failed!${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Base image built successfully!${NC}"
    echo ""
fi

# Build migration image (fast, uses cached base)
echo -e "${BLUE}Step 2/2: Building migration image: ${IMAGE_NAME}${NC}"
echo ""

docker build -t ${IMAGE_NAME} -f dockerfiles/test/Dockerfile .

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
    docker images | grep options-deep-test
    echo ""
    echo -e "${GREEN}You can now run integration tests with:${NC}"
    echo -e "${BLUE}  make integration-test${NC}"
    echo -e "${BLUE}  OR${NC}"
    echo -e "${BLUE}  ./tests/run_integration_tests.sh${NC}"
else
    echo -e "${RED}========================================================================${NC}"
    echo -e "${RED}✗ Image build failed!${NC}"
    echo -e "${RED}========================================================================${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}Build complete!${NC}"
