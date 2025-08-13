#!/bin/bash
set -e

echo "🚀 Starting comprehensive linting for Options-Deep project..."
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

print_warning() {
    echo -e "${YELLOW}$1${NC}"
}

print_error() {
    echo -e "${RED}$1${NC}"
}

# Track success/failure
ERRORS=0

print_step "📦 Sorting imports with isort..."
if uv run isort src/ tests/; then
    print_success "✅ Import sorting completed"
else
    print_error "❌ Import sorting failed"
    ERRORS=$((ERRORS + 1))
fi
echo ""

print_step "🎨 Formatting code with ruff..."
if uv run ruff format .; then
    print_success "✅ Code formatting completed"
else
    print_error "❌ Code formatting failed"
    ERRORS=$((ERRORS + 1))
fi
echo ""

print_step "🔍 Running ruff linter (with fixes)..."
if uv run ruff check --fix .; then
    print_success "✅ Ruff linting completed"
else
    print_warning "⚠️  Ruff found issues (some may require manual fixing)"
    ERRORS=$((ERRORS + 1))
fi
echo ""

print_step "🔍 Running mypy type checker..."
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
    print_success "🎉 All linting checks passed successfully!"
    echo ""
    print_step "📊 Quick stats:"
    echo "  - Import organization: ✅"
    echo "  - Code formatting: ✅" 
    echo "  - Linting rules: ✅"
    echo "  - Type checking: ✅"
    echo ""
    print_success "Your code is ready! 🚀"
    exit 0
else
    print_error "⚠️  $ERRORS linting step(s) had issues"
    echo ""
    print_step "💡 Next steps:"
    echo "  1. Review the output above for specific issues"
    echo "  2. Fix any remaining manual issues"
    echo "  3. Run 'make lint-check' to verify fixes"
    echo ""
    print_warning "Some issues may require manual intervention."
    exit 1
fi