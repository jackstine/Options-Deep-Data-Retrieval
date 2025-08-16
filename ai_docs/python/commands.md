# Python Command-Line Interface Patterns

## Overview

This document outlines the preferred approaches for creating command-line interfaces in Python projects, specifically for the Options-Deep application.

## Approach Comparison

### 1. Python Module Execution (Recommended)

**Pattern**: `python -m package.module.main`

**Advantages**:
- Uses Python's built-in module system
- No extra wrapper files needed
- Proper import resolution from project root
- Works with virtual environments automatically
- Standard Python practice

**Example**:
```bash
# Run NASDAQ screener sync
python -m src.cmd.nasdaq_screener_sync.main

# With arguments
python -m src.cmd.nasdaq_screener_sync.main --dry-run --verbose
```

**Implementation**:
```python
# src/cmd/nasdaq_screener_sync/main.py
#!/usr/bin/env python3
"""Main module with CLI functionality."""

def main():
    # CLI implementation
    pass

if __name__ == "__main__":
    main()
```

### 2. Direct Script Execution

**Pattern**: `python path/to/script.py`

**Advantages**:
- Simple and direct
- Good for standalone scripts

**Disadvantages**:
- Import path issues when script needs project modules
- Requires careful path management
- Not ideal for modular applications

### 3. Wrapper Scripts (Not Recommended)

**Pattern**: Creating additional wrapper scripts like `nasdaq_screener_sync.py`

**Why Not Recommended**:
- **Unnecessary complexity**: Adds extra files that just call other modules
- **Maintenance burden**: Another file to maintain and keep in sync
- **Import confusion**: Can create circular import issues
- **Non-standard**: Not the typical Python way to handle CLI commands

## Preferred Project Structure

```
src/
├── cmd/                          # Command-line interfaces
│   ├── __init__.py
│   ├── nasdaq_screener_sync/     # Specific command
│   │   ├── __init__.py
│   │   └── main.py              # CLI implementation
│   └── other_command/           # Additional commands
│       ├── __init__.py
│       └── main.py
```

## Command Implementation Best Practices

### 1. Main Module Structure

```python
#!/usr/bin/env python3
"""
Command description and usage examples.
"""

from __future__ import annotations
import argparse
import logging
import sys
from typing import Optional

def setup_logging(verbose: bool = False) -> None:
    """Configure logging based on verbosity level."""
    pass

def main() -> int:
    """
    Main entry point.
    
    Returns:
        Exit code: 0 for success, non-zero for error
    """
    parser = argparse.ArgumentParser(
        description="Command description",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Add arguments
    parser.add_argument("--verbose", "-v", action="store_true")
    
    args = parser.parse_args()
    
    try:
        # Command implementation
        return 0
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        return 1
    except Exception as e:
        logging.error(f"Command failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

### 2. Argument Parsing Standards

```python
# Standard argument patterns
parser.add_argument("--verbose", "-v", action="store_true", 
                   help="Enable verbose logging")
parser.add_argument("--dry-run", action="store_true",
                   help="Show what would be done without making changes")
parser.add_argument("--config", type=str, metavar="PATH",
                   help="Path to configuration file")
parser.add_argument("--output", "-o", type=str, metavar="FILE",
                   help="Output file path")
```

### 3. Error Handling

```python
def main() -> int:
    try:
        # Main logic
        result = perform_operation()
        
        if result.success:
            print(f"✅ Operation completed successfully")
            return 0
        else:
            print(f"⚠️ Operation completed with warnings")
            return 0
            
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        return 1
        
    except ValueError as e:
        print(f"❌ Invalid input: {e}")
        return 1
        
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        print(f"❌ Command failed: {e}")
        
        if args.verbose:
            import traceback
            traceback.print_exc()
        
        return 1
```

### 4. Logging Configuration

```python
def setup_logging(verbose: bool = False) -> None:
    """Set up logging with consistent format."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
```

## Running Commands

### Development Environment

```bash
# From project root directory
python -m src.cmd.nasdaq_screener_sync.main --help
python -m src.cmd.nasdaq_screener_sync.main --dry-run
python -m src.cmd.nasdaq_screener_sync.main --verbose
```

### Production Environment

```bash
# With virtual environment activated
python -m src.cmd.nasdaq_screener_sync.main

# Or with full path
/path/to/venv/bin/python -m src.cmd.nasdaq_screener_sync.main
```

## Advanced Patterns

### 1. Setup.py Entry Points (For Installed Packages)

If the package is installed, you can define entry points in `setup.py`:

```python
# setup.py
setup(
    name="options-deep",
    entry_points={
        'console_scripts': [
            'nasdaq-sync=src.cmd.nasdaq_screener_sync.main:main',
        ],
    },
)
```

Then after installation:
```bash
nasdaq-sync --help
```

### 2. Makefile Commands

```makefile
# Makefile
nasdaq-sync:
	python -m src.cmd.nasdaq_screener_sync.main

nasdaq-sync-dry:
	python -m src.cmd.nasdaq_screener_sync.main --dry-run

.PHONY: nasdaq-sync nasdaq-sync-dry
```

Usage:
```bash
make nasdaq-sync
make nasdaq-sync-dry
```

### 3. Multiple Commands in One Module

```python
# src/cmd/main.py
def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')
    
    # NASDAQ sync command
    nasdaq_parser = subparsers.add_parser('nasdaq-sync')
    nasdaq_parser.add_argument('--dry-run', action='store_true')
    
    # Other commands...
    
    args = parser.parse_args()
    
    if args.command == 'nasdaq-sync':
        from src.cmd.nasdaq_screener_sync.main import main as nasdaq_main
        return nasdaq_main()
```

## Recommendations for Options-Deep

1. **Use Python module execution**: `python -m src.cmd.command.main`
2. **No wrapper scripts**: Keep it simple with direct module execution
3. **Consistent argument patterns**: Follow the established patterns shown above
4. **Proper error handling**: Always return appropriate exit codes
5. **Logging integration**: Use the project's logging configuration
6. **Documentation**: Include usage examples in module docstrings

## Current Commands

### NASDAQ Screener Sync

**Purpose**: Synchronize NASDAQ screener CSV data with the database

**Usage**:
```bash
# Basic sync
python -m src.cmd.nasdaq_screener_sync.main

# Dry run to preview changes
python -m src.cmd.nasdaq_screener_sync.main --dry-run

# Verbose output
python -m src.cmd.nasdaq_screener_sync.main --verbose

# Custom screener directory
python -m src.cmd.nasdaq_screener_sync.main --screener-dir /path/to/files
```

**Features**:
- Validates screener directory and CSV files
- Shows preview of changes in dry-run mode
- Comprehensive error handling and logging
- Progress reporting and result summary