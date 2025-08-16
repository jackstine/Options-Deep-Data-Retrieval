# Practical Implementation Guide: Python Linting Tools

## Executive Summary

This guide provides step-by-step implementation instructions for setting up modern Python linting workflows. It covers three primary approaches: the recommended modern toolchain (UV + Ruff), traditional comprehensive setup, and hybrid approaches for different team needs and project requirements.

## 1. Quick Start: Modern Toolchain (Recommended)

### Prerequisites
- Python 3.8+ installed
- Command line access
- Git repository initialized

### Step 1: Install UV
```bash
# Install UV (cross-platform)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Alternative: Using pip if available
pip install uv

# Verify installation
uv --version
```

### Step 2: Initialize Project with Modern Linting
```bash
# Create new project (or navigate to existing)
uv init options-deep-linting --python 3.11
cd options-deep-linting

# Add development dependencies for linting
uv add --dev ruff mypy bandit pre-commit

# Add your project dependencies
uv add fastapi pydantic sqlalchemy
```

### Step 3: Configure Linting Tools
```toml
# pyproject.toml (automatically created, add tool configurations)
[project]
name = "options-deep-linting"
version = "0.1.0"
description = "Modern Python linting setup"
dependencies = [
    "fastapi>=0.104.0",
    "pydantic>=2.5.0",
    "sqlalchemy>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "ruff>=0.1.7",
    "mypy>=1.7.0",
    "bandit[toml]>=1.7.5",
    "pre-commit>=3.6.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

# Ruff configuration
[tool.ruff]
target-version = "py311"
line-length = 88
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
    "N",  # pep8-naming
]
ignore = [
    "E501",  # line too long (handled by formatter)
    "B008",  # do not perform function calls in argument defaults
]
exclude = [
    "migrations/",
    "venv/",
    ".git/",
    "__pycache__/",
    "*.pyc",
]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
docstring-code-format = true

[tool.ruff.per-file-ignores]
"tests/*" = ["D", "ANN"]
"scripts/*" = ["T201"]  # Allow print statements
"__init__.py" = ["F401"]  # Allow unused imports

# mypy configuration
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_reexport = true
warn_redundant_casts = true
warn_unused_ignores = true
show_error_codes = true

# Bandit security configuration
[tool.bandit]
exclude_dirs = ["tests", "venv", ".venv"]
severity = "medium"
confidence = "medium"
skips = ["B101", "B102"]  # Skip assert and hardcoded_password_funcarg

[tool.bandit.assert_used]
skips = ["*_test.py", "*test_*.py"]
```

### Step 4: Set Up Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.7
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        language: system
        entry: uv run mypy
        pass_filenames: false
        args: [src/]

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        language: system
        entry: uv run bandit
        args: [-r, src/, -ll]
```

### Step 5: Initialize Pre-commit
```bash
# Install pre-commit hooks
uv run pre-commit install

# Test the hooks on all files
uv run pre-commit run --all-files
```

### Step 6: Create Development Scripts
```bash
# Create scripts directory
mkdir scripts

# Create lint.sh script
cat > scripts/lint.sh << 'EOF'
#!/bin/bash
set -e

echo "🔍 Running Ruff linter..."
uv run ruff check --fix .

echo "🎨 Running Ruff formatter..."
uv run ruff format .

echo "🔍 Running mypy type checker..."
uv run mypy src/

echo "🔒 Running Bandit security scanner..."
uv run bandit -r src/ -ll

echo "✅ All linting checks passed!"
EOF

chmod +x scripts/lint.sh
```

### Step 7: Test Your Setup
```python
# Create src/example.py to test linting
mkdir -p src/example
cat > src/example/__init__.py << 'EOF'
"""Example module for testing linting setup."""
EOF

cat > src/example/main.py << 'EOF'
"""Example module demonstrating linting setup."""
from typing import List, Optional
import os

def process_data(items: List[str], filter_empty: bool = True) -> List[str]:
    """Process a list of strings, optionally filtering empty ones.
    
    Args:
        items: List of strings to process
        filter_empty: Whether to filter out empty strings
        
    Returns:
        Processed list of strings
    """
    if filter_empty:
        return [item.strip() for item in items if item.strip()]
    return [item.strip() for item in items]

def get_config_value(key: str) -> Optional[str]:
    """Get configuration value from environment.
    
    Args:
        key: Configuration key name
        
    Returns:
        Configuration value or None if not found
    """
    return os.getenv(key)

if __name__ == "__main__":
    sample_data = ["  hello  ", "", "world", "  "]
    result = process_data(sample_data)
    print(f"Processed data: {result}")
EOF
```

### Step 8: Run Complete Linting Check
```bash
# Run all linting tools
./scripts/lint.sh

# Or run individually
uv run ruff check --fix .
uv run ruff format .
uv run mypy src/
uv run bandit -r src/ -ll
```

### Step 9: Set Up CI/CD (GitHub Actions)
```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline
on: 
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout code
      uses: actions/checkout@v4
    
    - name: Install UV
      run: curl -LsSf https://astral.sh/uv/install.sh | sh
    
    - name: Set up Python
      run: uv python install 3.11
    
    - name: Install dependencies
      run: uv sync --all-extras --dev
    
    - name: Cache UV dependencies
      uses: actions/cache@v3
      with:
        path: |
          ~/.cache/uv
          .venv
        key: ${{ runner.os }}-uv-${{ hashFiles('**/uv.lock') }}
        restore-keys: |
          ${{ runner.os }}-uv-
    
    - name: Run Ruff linter
      run: uv run ruff check --output-format=github .
    
    - name: Run Ruff formatter check
      run: uv run ruff format --check .
    
    - name: Run mypy type checker
      run: uv run mypy src/
    
    - name: Run Bandit security scanner
      run: uv run bandit -r src/ -f json -o bandit-report.json || true
    
    - name: Upload Bandit results
      uses: actions/upload-artifact@v3
      if: always()
      with:
        name: bandit-security-report
        path: bandit-report.json
    
    - name: Run pre-commit hooks
      run: uv run pre-commit run --all-files
```

## 2. Traditional Comprehensive Setup

### For teams preferring established tools or requiring specific plugins

### Step 1: Install Traditional Tools
```bash
# Using pip (or adapt for poetry/pipenv)
pip install --upgrade pip

# Install core linting tools
pip install black isort flake8 pylint mypy bandit

# Install useful Flake8 plugins
pip install flake8-bugbear flake8-comprehensions flake8-docstrings flake8-import-order

# Install pre-commit
pip install pre-commit
```

### Step 2: Create Configuration Files
```ini
# setup.cfg (or use pyproject.toml)
[flake8]
max-line-length = 88
extend-ignore = E203, E501, W503
per-file-ignores =
    __init__.py:F401
    tests/*:D
exclude = 
    .git,
    __pycache__,
    venv,
    .venv,
    migrations
select = E,W,F,B,C4
```

```toml
# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py38', 'py39', 'py310', 'py311']
include = '\.pyi?$'
exclude = '''
/(
    \.git
  | \.mypy_cache
  | \.tox
  | \.venv
  | venv
  | _build
  | buck-out
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
known_first_party = ["src"]
known_third_party = ["fastapi", "pydantic", "sqlalchemy"]
sections = ["FUTURE", "STDLIB", "THIRDPARTY", "FIRSTPARTY", "LOCALFOLDER"]

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
ignore_missing_imports = true

[tool.pylint.main]
max-line-length = 88
disable = [
    "C0103",  # Invalid name
    "R0903",  # Too few public methods
    "R0801",  # Similar lines in files
]

[tool.bandit]
exclude_dirs = ["tests", "venv"]
severity = "medium"
confidence = "medium"
```

### Step 3: Traditional Pre-commit Setup
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        additional_dependencies: [
          flake8-bugbear,
          flake8-comprehensions,
          flake8-docstrings
        ]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: [-ll]
```

### Step 4: Traditional Makefile/Scripts
```makefile
# Makefile
.PHONY: lint format typecheck security test

lint:
	flake8 src/ tests/
	
format:
	black src/ tests/
	isort src/ tests/

typecheck:
	mypy src/

security:
	bandit -r src/

check: format lint typecheck security
	@echo "All checks passed!"

install-dev:
	pip install -r requirements-dev.txt
	pre-commit install
```

## 3. Hybrid Approach Setup

### For teams migrating gradually or needing specific tool combinations

### Configuration Example
```toml
# pyproject.toml - Hybrid approach
[tool.ruff]
# Use Ruff for basic linting and formatting (fast)
target-version = "py311"
line-length = 88
select = ["E", "W", "F", "I"]  # Basic rules only
format.quote-style = "double"

[tool.flake8]
# Use Flake8 for comprehensive checking (slower, but thorough)
max-line-length = 88
extend-ignore = ["E203", "E501"]
per-file-ignores = ["__init__.py:F401"]

[tool.mypy]
python_version = "3.11"
strict = true

[tool.bandit]
severity = "high"  # Only high-severity issues
```

### Hybrid Script
```bash
#!/bin/bash
# scripts/hybrid-lint.sh

echo "🚀 Fast formatting with Ruff..."
ruff format .

echo "🔍 Basic linting with Ruff..."  
ruff check --fix .

echo "🧐 Comprehensive analysis with Flake8..."
flake8 src/

echo "🔍 Type checking with mypy..."
mypy src/

echo "🔒 Security scan with Bandit..."
bandit -r src/ -ll

echo "✅ Hybrid linting complete!"
```

## 4. IDE Integration Setup

### VS Code Configuration
```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.linting.mypyEnabled": true,
    "python.linting.banditEnabled": true,
    "python.formatting.provider": "ruff",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true,
        "source.fixAll": true
    },
    "python.analysis.typeCheckingMode": "basic",
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        ".mypy_cache": true,
        ".ruff_cache": true
    }
}
```

### PyCharm Configuration
```xml
<!-- .idea/inspectionProfiles/profiles_settings.xml -->
<component name="InspectionProjectProfileManager">
  <settings>
    <option name="USE_PROJECT_PROFILE" value="true" />
    <version value="1.0" />
  </settings>
</component>
```

### Vim/Neovim Configuration
```lua
-- init.lua (for Neovim)
local lspconfig = require('lspconfig')

-- Ruff LSP
lspconfig.ruff_lsp.setup {
  init_options = {
    settings = {
      args = {},
    }
  }
}

-- mypy LSP
lspconfig.pyright.setup {
  settings = {
    python = {
      analysis = {
        typeCheckingMode = "basic",
      },
    },
  },
}
```

## 5. Docker Integration

### Dockerfile with Linting
```dockerfile
# Dockerfile.lint
FROM python:3.11-slim

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app
COPY . /app

# Install dependencies
RUN uv sync --dev --frozen

# Run linting
RUN uv run ruff check .
RUN uv run ruff format --check .
RUN uv run mypy src/
RUN uv run bandit -r src/

CMD ["echo", "Linting complete!"]
```

### Docker Compose Development
```yaml
# docker-compose.yml
version: '3.8'
services:
  lint:
    build:
      context: .
      dockerfile: Dockerfile.lint
    volumes:
      - .:/app
    command: |
      sh -c "
        uv run ruff check --fix . &&
        uv run ruff format . &&
        uv run mypy src/ &&
        uv run bandit -r src/
      "
  
  dev:
    build: .
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    environment:
      - PYTHONPATH=/app/src
    command: uv run uvicorn src.main:app --reload --host 0.0.0.0
```

## 6. Advanced Configuration Examples

### Complex Project Structure
```
project/
├── src/
│   ├── api/          # REST API code
│   ├── models/       # Data models  
│   ├── services/     # Business logic
│   └── utils/        # Utility functions
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── scripts/          # Development scripts
├── migrations/       # Database migrations
└── docs/            # Documentation
```

### Per-Directory Linting Rules
```toml
[tool.ruff.per-file-ignores]
# API routes can have more complex functions
"src/api/*" = ["C901"]  # Allow complex functions

# Models can have many attributes
"src/models/*" = ["R0902"]  # Too many instance attributes

# Tests can use asserts and have long lines
"tests/*" = ["D", "ANN", "S101", "E501"]

# Scripts can use print statements
"scripts/*" = ["T201"]

# Migrations are auto-generated
"migrations/*" = ["ALL"]

# Allow imports in __init__.py files
"**/__init__.py" = ["F401", "F403"]
```

### Environment-Specific Configuration
```toml
# Development environment
[tool.ruff.extend-per-file-ignores]
"src/debug.py" = ["T201", "F401"]  # Allow debugging code

# CI environment - stricter rules
[tool.ruff.ci]
select = ["ALL"]
ignore = []
```

## 7. Performance Optimization Tips

### UV Performance Optimization
```bash
# Use lockfile for faster installs in CI
uv sync --frozen

# Parallel installation
uv sync --no-build-isolation

# Custom cache directory for CI
export UV_CACHE_DIR="/tmp/uv-cache"
uv sync
```

### Ruff Performance Optimization
```toml
[tool.ruff]
# Enable caching (default, but explicit)
cache-dir = ".ruff_cache"

# Only check necessary files
include = ["*.py", "*.pyi", "**/pyproject.toml"]
exclude = [
    "node_modules/",
    "dist/",
    "build/",
    ".git/",
]

# Limit rule set for faster execution
select = ["E", "W", "F", "I"]  # Essential rules only
```

### CI/CD Performance Tips
```yaml
# GitHub Actions optimization
- name: Cache dependencies
  uses: actions/cache@v3
  with:
    path: |
      ~/.cache/uv
      .venv
      .mypy_cache
      .ruff_cache
    key: ${{ runner.os }}-python-${{ hashFiles('**/uv.lock') }}
    
- name: Parallel linting
  run: |
    # Run fast checks first
    uv run ruff check . &
    uv run ruff format --check . &
    wait
    
    # Then slower checks
    uv run mypy src/ &
    uv run bandit -r src/ &
    wait
```

## 8. Troubleshooting Common Issues

### Issue: Ruff and Black Conflicts
```toml
# Solution: Use Ruff format instead of Black
[tool.ruff.format]
quote-style = "double"  # Match Black's default
line-ending = "auto"    # Match Black's behavior
```

### Issue: mypy Import Errors
```toml
[tool.mypy]
# Solution: Configure module search paths
mypy_path = "src"
namespace_packages = true
explicit_package_bases = true

# Ignore missing imports for third-party packages
[[tool.mypy.overrides]]
module = [
    "third_party_package.*",
    "another_package.*"
]
ignore_missing_imports = true
```

### Issue: Pre-commit Hooks Failing
```bash
# Debug pre-commit issues
pre-commit run --all-files --verbose

# Update hook versions
pre-commit autoupdate

# Skip specific hooks temporarily
SKIP=mypy pre-commit run --all-files
```

### Issue: UV Virtual Environment Issues
```bash
# Reset virtual environment
rm -rf .venv
uv sync

# Force recreation
uv sync --reinstall

# Use system Python instead of UV-managed
uv sync --python-preference system
```

## 9. Monitoring and Metrics

### Code Quality Metrics Script
```python
#!/usr/bin/env python3
"""Code quality metrics collection script."""

import subprocess
import json
from pathlib import Path

def run_command(cmd):
    """Run shell command and return output."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def collect_metrics():
    """Collect code quality metrics."""
    metrics = {}
    
    # Ruff violations
    code, stdout, _ = run_command("uv run ruff check --statistics --format json .")
    if code == 0:
        try:
            ruff_data = json.loads(stdout)
            metrics['ruff_violations'] = sum(len(file['messages']) for file in ruff_data)
        except:
            metrics['ruff_violations'] = 0
    
    # mypy errors  
    code, stdout, _ = run_command("uv run mypy src/ --json-report /tmp/mypy-report")
    if code == 0:
        try:
            with open('/tmp/mypy-report/index.json') as f:
                mypy_data = json.load(f)
                metrics['mypy_errors'] = mypy_data.get('summary', {}).get('error_count', 0)
        except:
            metrics['mypy_errors'] = 0
    
    # Bandit issues
    code, stdout, _ = run_command("uv run bandit -r src/ -f json")
    if stdout:
        try:
            bandit_data = json.loads(stdout)
            metrics['security_issues'] = len(bandit_data.get('results', []))
        except:
            metrics['security_issues'] = 0
    
    # Lines of code
    code, stdout, _ = run_command("find src/ -name '*.py' -exec wc -l {} + | tail -n 1")
    if code == 0:
        try:
            metrics['lines_of_code'] = int(stdout.split()[0])
        except:
            metrics['lines_of_code'] = 0
    
    return metrics

if __name__ == "__main__":
    metrics = collect_metrics()
    print("Code Quality Metrics:")
    for key, value in metrics.items():
        print(f"  {key}: {value}")
    
    # Save to file for CI/CD
    with open('quality-metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)
```

### GitHub Actions Metrics Collection
```yaml
- name: Collect Quality Metrics
  run: |
    python scripts/collect_metrics.py
    
- name: Comment PR with Metrics
  uses: actions/github-script@v6
  if: github.event_name == 'pull_request'
  with:
    script: |
      const fs = require('fs');
      const metrics = JSON.parse(fs.readFileSync('quality-metrics.json', 'utf8'));
      
      const comment = `## Code Quality Metrics
      - Ruff violations: ${metrics.ruff_violations}
      - mypy errors: ${metrics.mypy_errors}  
      - Security issues: ${metrics.security_issues}
      - Lines of code: ${metrics.lines_of_code}`;
      
      github.rest.issues.createComment({
        issue_number: context.issue.number,
        owner: context.repo.owner,
        repo: context.repo.repo,
        body: comment
      });
```

## 10. Final Recommendations

### For Options-Deep Project Specifically
```bash
# Recommended setup for Options-Deep
cd /Users/jake/Projects/OptionsDeep/AI/Options-Deep

# Install UV if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add linting dependencies to existing project
uv add --dev ruff mypy bandit pre-commit

# Add ruff configuration to existing pyproject.toml
# (Use configuration from Step 3 above)

# Initialize pre-commit
uv run pre-commit install
```

### Team Adoption Strategy
1. **Week 1-2**: Install and configure tools
2. **Week 3-4**: Run tools manually, fix major issues
3. **Week 5-6**: Enable pre-commit hooks
4. **Week 7-8**: Integrate with CI/CD pipeline
5. **Ongoing**: Regular rule updates and team training

### Success Metrics
- Reduced code review time (target: 25% reduction)
- Fewer production bugs (target: 30% reduction)  
- Improved developer satisfaction (survey-based)
- Faster CI/CD pipelines (target: 50% reduction in linting time)

This implementation guide provides everything needed to set up professional-grade Python linting workflows, from quick modern setups to comprehensive traditional approaches, with specific attention to the Options-Deep project's needs and structure.