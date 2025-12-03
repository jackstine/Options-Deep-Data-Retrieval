# install dependencies using uv
PHONY: install
install:
	uv sync

# install development dependencies using uv
PHONY: install-dev
install-dev:
	uv sync --dev

# run all unit tests
PHONY: unit-test
unit-test:
	OPTIONS_DEEP_ENV=unittest PYTHONPATH=. python -m unittest discover -s src -p "test_*.py" -v

# run integration tests
PHONY: integration-test
integration-test:
	@echo "🧪 Running integration tests..."
	@bash tests/run_integration_tests.sh

# run all tests (unit + integration)
PHONY: test-all
test-all: unit-test integration-test
	@echo "✅ All tests completed!"

# Docker Commands - Multi-Stage Build

# build base image with dependencies (rarely rebuilt)
PHONY: build-base-image
build-base-image:
	@echo "🐳 Building base Docker image (dependencies only)..."
	@docker build --target base -t options-deep-test-base:latest -f dockerfiles/test/Dockerfile .
	@echo "✅ Base image built successfully!"

# rebuild base image (force rebuild without cache)
PHONY: rebuild-base-image
rebuild-base-image:
	@echo "🐳 Rebuilding base Docker image (no cache)..."
	@docker build --no-cache --target base -t options-deep-test-base:latest -f dockerfiles/test/Dockerfile .
	@echo "✅ Base image rebuilt successfully!"

# build test Docker image with pre-applied migrations (uses cached base)
PHONY: build-test-image
build-test-image:
	@echo "🐳 Building test Docker image..."
	@bash scripts/build_test_image.sh

# rebuild test image (force rebuild without cache)
PHONY: rebuild-test-image
rebuild-test-image:
	@echo "🐳 Rebuilding test Docker image (no cache)..."
	@docker build --no-cache -t options-deep-test:latest -f dockerfiles/test/Dockerfile .
	@echo "✅ Test image rebuilt successfully!"

# remove test Docker images (both base and migration)
PHONY: clean-test-image
clean-test-image:
	@echo "🗑️  Removing test Docker images..."
	@docker rmi options-deep-test:latest || true
	@docker rmi options-deep-test-base:latest || true
	@echo "✅ Test images removed!"

# build test data Docker image with pre-populated fixtures (builds on options-deep-test:latest)
PHONY: build-test-data-image
build-test-data-image:
	@echo "🐳 Building test data Docker image with fixtures..."
	@bash scripts/build_test_data_image.sh

# rebuild test data image (force rebuild without cache)
PHONY: rebuild-test-data-image
rebuild-test-data-image:
	@echo "🐳 Rebuilding test data Docker image (no cache)..."
	@docker build --no-cache -t options-deep-test-data:latest -f dockerfiles/test/Dockerfile.data .
	@echo "✅ Test data image rebuilt successfully!"

# remove test data Docker image
PHONY: clean-test-data-image
clean-test-data-image:
	@echo "🗑️  Removing test data Docker image..."
	@docker rmi options-deep-test-data:latest || true
	@echo "✅ Test data image removed!"

# remove all test Docker images (base, schema, and data)
PHONY: clean-all-test-images
clean-all-test-images: clean-test-data-image clean-test-image
	@echo "✅ All test images removed!"

# Linting Commands

# run ruff linter with automatic fixes
PHONY: lint
lint:
	uv run ruff check --fix .

# format code using ruff formatter
PHONY: format
format:
	uv run ruff format .

# run mypy type checker
PHONY: type-check
type-check:
	uv run mypy src/

# sort imports using isort
# ruff will sort the packages
# PHONY: sort-imports
# sort-imports:
# 	uv run isort src/ tests/

# run complete linting suite with fixes
PHONY: lint-all
lint-all: sort-imports format lint type-check
	@echo "✅ All linting completed!"

# check code without making changes (CI-friendly)
PHONY: lint-check
lint-check:
	uv run ruff check --diff .
	uv run ruff format --check .
	uv run mypy src/
	uv run isort --check-only --diff src/ tests/

# show linting statistics
PHONY: lint-stats
lint-stats:
	@echo "📊 Linting Statistics:"
	@echo "Ruff violations:"
	@uv run ruff check --statistics . || true
	@echo "\nMypy report:"
	@uv run mypy src/ --report /tmp/mypy-report --html-report /tmp/mypy-html || true
	@echo "Mypy report generated in /tmp/mypy-report/"

# fix all auto-fixable issues
PHONY: lint-fix
lint-fix:
	uv run ruff check --fix .
	uv run ruff format .
	@echo "✅ Auto-fixable issues resolved!"


