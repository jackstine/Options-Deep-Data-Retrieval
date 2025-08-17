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
	PYTHONPATH=. python -m unittest discover -s tests -p "test_*.py" -v

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