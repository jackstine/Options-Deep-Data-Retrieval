# Python Single Executable Programs

## Overview

This document outlines the proper Python patterns for creating single executable programs - standalone scripts that can be run directly as complete applications, as opposed to modules within a larger project structure.

## When to Use Single Executable Programs vs. Project Modules

### Single Executable Programs
**Use when**:
- Creating standalone utilities or tools
- Building simple scripts for automation
- Developing one-off data processing scripts
- Creating demonstration or example programs
- Building tools that will be distributed independently

**Examples**:
- Data migration scripts
- File processing utilities
- System administration tools
- Quick analysis scripts

### Project Modules (like our `src/cmd/` structure)
**Use when**:
- Building commands as part of a larger application
- Commands need to import project-specific modules
- Multiple related commands share common functionality
- Commands are part of an application's feature set

## Single Executable Program Patterns

### 1. Basic Executable Script Pattern

```python
#!/usr/bin/env python3
"""
Single-purpose script description.

This script does X, Y, and Z.
Usage examples and documentation go here.
"""

from __future__ import annotations
import argparse
import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the script."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def process_data(input_file: Path, output_file: Optional[Path] = None) -> bool:
    """
    Main processing function.
    
    Args:
        input_file: Path to input file
        output_file: Optional output file path
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Main logic here
        logging.info(f"Processing {input_file}")
        
        # Example processing
        with open(input_file, 'r') as f:
            data = f.read()
        
        # Process data...
        processed_data = data.upper()  # Example transformation
        
        # Write output
        if output_file:
            with open(output_file, 'w') as f:
                f.write(processed_data)
            logging.info(f"Output written to {output_file}")
        else:
            print(processed_data)
        
        return True
        
    except Exception as e:
        logging.error(f"Processing failed: {e}")
        return False


def main() -> int:
    """
    Main entry point.
    
    Returns:
        Exit code: 0 for success, 1+ for error
    """
    parser = argparse.ArgumentParser(
        description="Process data files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "input_file",
        type=Path,
        help="Input file to process"
    )
    
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output file (default: stdout)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    # Validate inputs
    if not args.input_file.exists():
        print(f"Error: Input file does not exist: {args.input_file}")
        return 1
    
    if not args.input_file.is_file():
        print(f"Error: Input path is not a file: {args.input_file}")
        return 1
    
    try:
        success = process_data(args.input_file, args.output)
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
        
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

### 2. Making Scripts Executable

#### Method 1: Shebang Line (Unix/Linux/macOS)

```python
#!/usr/bin/env python3
# Script content...
```

Then make executable:
```bash
chmod +x script.py
./script.py --help
```

#### Method 2: Python Entry Points (setup.py)

```python
# setup.py
from setuptools import setup

setup(
    name="my-tools",
    version="1.0.0",
    py_modules=["my_script"],
    entry_points={
        'console_scripts': [
            'my-tool=my_script:main',
        ],
    },
)
```

After installation:
```bash
pip install .
my-tool --help
```

#### Method 3: Direct Execution

```bash
python script.py --help
python3 script.py --help
```

### 3. Advanced Executable Script Pattern

```python
#!/usr/bin/env python3
"""
Advanced single executable script with configuration and multiple operations.

This script demonstrates advanced patterns for standalone Python programs.
"""

from __future__ import annotations
import argparse
import configparser
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


@dataclass
class Config:
    """Configuration settings for the script."""
    verbose: bool = False
    dry_run: bool = False
    input_dir: Optional[Path] = None
    output_dir: Optional[Path] = None
    file_patterns: List[str] = None
    
    def __post_init__(self):
        if self.file_patterns is None:
            self.file_patterns = ["*.txt", "*.csv"]


class ScriptError(Exception):
    """Custom exception for script-specific errors."""
    pass


class DataProcessor:
    """Main processing class for the script."""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def validate_inputs(self) -> None:
        """Validate configuration and inputs."""
        if not self.config.input_dir or not self.config.input_dir.exists():
            raise ScriptError(f"Input directory does not exist: {self.config.input_dir}")
        
        if self.config.output_dir:
            self.config.output_dir.mkdir(parents=True, exist_ok=True)
    
    def find_files(self) -> List[Path]:
        """Find files matching configured patterns."""
        files = []
        for pattern in self.config.file_patterns:
            files.extend(self.config.input_dir.glob(pattern))
        
        self.logger.info(f"Found {len(files)} files to process")
        return sorted(files)
    
    def process_file(self, file_path: Path) -> bool:
        """Process a single file."""
        try:
            self.logger.debug(f"Processing {file_path}")
            
            if self.config.dry_run:
                self.logger.info(f"[DRY RUN] Would process {file_path}")
                return True
            
            # Actual processing logic here
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Example: convert to uppercase
            processed_content = content.upper()
            
            # Write output
            if self.config.output_dir:
                output_path = self.config.output_dir / file_path.name
                with open(output_path, 'w') as f:
                    f.write(processed_content)
                self.logger.info(f"Wrote {output_path}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error processing {file_path}: {e}")
            return False
    
    def run(self) -> bool:
        """Run the main processing logic."""
        try:
            self.validate_inputs()
            files = self.find_files()
            
            if not files:
                self.logger.warning("No files found to process")
                return True
            
            success_count = 0
            for file_path in files:
                if self.process_file(file_path):
                    success_count += 1
            
            self.logger.info(f"Successfully processed {success_count}/{len(files)} files")
            return success_count == len(files)
            
        except ScriptError as e:
            self.logger.error(f"Script error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return False


def load_config_file(config_path: Path) -> Dict[str, Any]:
    """Load configuration from file."""
    if config_path.suffix.lower() == '.json':
        with open(config_path) as f:
            return json.load(f)
    
    elif config_path.suffix.lower() in ['.ini', '.cfg']:
        parser = configparser.ConfigParser()
        parser.read(config_path)
        return dict(parser['DEFAULT']) if 'DEFAULT' in parser else {}
    
    else:
        raise ValueError(f"Unsupported config file format: {config_path.suffix}")


def setup_logging(verbose: bool = False, log_file: Optional[Path] = None) -> None:
    """Configure logging with optional file output."""
    level = logging.DEBUG if verbose else logging.INFO
    
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=handlers
    )


def create_config_from_args(args: argparse.Namespace) -> Config:
    """Create configuration object from command line arguments."""
    config = Config()
    
    # Load from config file if provided
    if args.config:
        try:
            file_config = load_config_file(args.config)
            # Apply file config (implementation depends on format)
            for key, value in file_config.items():
                if hasattr(config, key):
                    setattr(config, key, value)
        except Exception as e:
            logging.error(f"Error loading config file: {e}")
            sys.exit(1)
    
    # Override with command line arguments
    config.verbose = args.verbose
    config.dry_run = args.dry_run
    config.input_dir = args.input_dir
    config.output_dir = args.output_dir
    
    if args.patterns:
        config.file_patterns = args.patterns
    
    return config


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Advanced data processing script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "input_dir",
        type=Path,
        help="Input directory containing files to process"
    )
    
    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        help="Output directory for processed files"
    )
    
    parser.add_argument(
        "-c", "--config",
        type=Path,
        help="Configuration file (JSON or INI format)"
    )
    
    parser.add_argument(
        "-p", "--patterns",
        nargs="+",
        help="File patterns to match (default: *.txt *.csv)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--log-file",
        type=Path,
        help="Write logs to file"
    )
    
    args = parser.parse_args()
    
    # Setup logging first
    setup_logging(args.verbose, args.log_file)
    
    # Create configuration
    config = create_config_from_args(args)
    
    # Run processor
    processor = DataProcessor(config)
    
    try:
        success = processor.run()
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1


if __name__ == "__main__":
    sys.exit(main())
```

## Distribution and Packaging

### 1. Single File Distribution

For simple scripts, you can distribute as a single `.py` file:

```python
#!/usr/bin/env python3
"""
Standalone script - all dependencies should be standard library.
"""
# Keep imports to standard library only for portability
import argparse
import json
import sys
from pathlib import Path

# All code in single file
```

### 2. Package with Dependencies

For scripts with external dependencies, create a proper package:

```
my_script/
├── setup.py
├── requirements.txt
├── my_script.py
└── README.md
```

```python
# setup.py
from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt", "r") as fh:
    requirements = [line.strip() for line in fh if line.strip()]

setup(
    name="my-script",
    version="1.0.0",
    author="Your Name",
    description="Description of your script",
    long_description=long_description,
    long_description_content_type="text/markdown",
    py_modules=["my_script"],
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "my-script=my_script:main",
        ],
    },
    python_requires=">=3.9",
)
```

### 3. Using PyInstaller for True Executables

Convert Python scripts to standalone executables:

```bash
pip install pyinstaller
pyinstaller --onefile script.py
```

This creates a single executable file that includes Python and all dependencies.

## Best Practices for Single Executable Programs

### 1. Structure
- Use `if __name__ == "__main__":` guard
- Implement proper `main()` function that returns exit codes
- Keep all logic in functions, not at module level

### 2. Error Handling
- Use appropriate exit codes (0 = success, 1+ = error)
- Handle `KeyboardInterrupt` gracefully
- Provide meaningful error messages

### 3. Configuration
- Support command-line arguments
- Consider configuration files for complex options
- Use environment variables when appropriate

### 4. Logging
- Implement proper logging instead of print statements
- Support verbose/debug modes
- Consider log file output for long-running scripts

### 5. Dependencies
- Minimize external dependencies for portability
- Use standard library when possible
- Document all requirements clearly

### 6. Documentation
- Include comprehensive docstrings
- Provide usage examples in module docstring
- Create README.md for distributed scripts

## Examples in Options-Deep Context

### Single Executable for Data Migration

```python
#!/usr/bin/env python3
"""
Standalone data migration script for Options-Deep.

This script can be run independently to migrate data between systems.
It includes all necessary database connection logic.
"""

import argparse
import os
import sys
from pathlib import Path

# Minimal imports - could be distributed as single file
import json
import logging
from datetime import datetime

def main():
    # Implementation here
    pass

if __name__ == "__main__":
    sys.exit(main())
```

### Quick Analysis Script

```python
#!/usr/bin/env python3
"""
Quick stock data analysis script.

Analyzes CSV files and outputs summary statistics.
"""

import csv
import statistics
from pathlib import Path

def analyze_stock_data(csv_file: Path):
    prices = []
    with open(csv_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            prices.append(float(row['price']))
    
    return {
        'count': len(prices),
        'mean': statistics.mean(prices),
        'median': statistics.median(prices),
        'stdev': statistics.stdev(prices) if len(prices) > 1 else 0
    }

def main():
    # Implementation
    pass

if __name__ == "__main__":
    sys.exit(main())
```

## Summary

- **Single executable programs** are best for standalone utilities and tools
- **Project modules** (like our `src/cmd/` structure) are better for integrated application commands
- Use proper Python patterns: shebang lines, `main()` functions, exit codes
- Keep dependencies minimal for portability
- Implement proper error handling and logging
- Consider distribution method based on complexity and target audience