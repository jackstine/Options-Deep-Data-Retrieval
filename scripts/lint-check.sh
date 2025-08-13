#!/bin/bash
set -e

echo "🔍 Running linting checks (CI-friendly, no modifications)..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${BLUE}$1${NC}"
}

print_success() {
    echo -e "${GREEN}$1${NC}"
}

print_error() {
    echo -e "${RED}$1${NC}"
}

# Track success/failure
ERRORS=0

print_step "📦 Checking import sorting..."
if uv run isort --check-only --diff src/ tests/; then
    print_success "✅ Import sorting is correct"
else
    print_error "❌ Import sorting issues found"
    ERRORS=$((ERRORS + 1))
fi
echo ""

print_step "🎨 Checking code formatting..."
if uv run ruff format --check .; then
    print_success "✅ Code formatting is correct"
else
    print_error "❌ Code formatting issues found"
    ERRORS=$((ERRORS + 1))
fi
echo ""

print_step "🔍 Checking linting rules..."
if uv run ruff check --diff .; then
    print_success "✅ No linting violations"
else
    print_error "❌ Linting violations found"
    ERRORS=$((ERRORS + 1))
fi
echo ""

print_step "🔍 Running type checking..."
if uv run mypy src/; then
    print_success "✅ Type checking passed"
else
    print_error "❌ Type checking failed"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Summary
echo "==============================================="
if [ $ERRORS -eq 0 ]; then
    print_success "🎉 All linting checks passed! Code is ready for CI/CD."
    exit 0
else
    print_error "❌ $ERRORS linting check(s) failed"
    echo ""
    echo "💡 To fix issues automatically, run:"
    echo "   ./scripts/lint.sh"
    echo "   or"
    echo "   make lint-all"
    echo ""
    exit 1
fi