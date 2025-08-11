#!/usr/bin/env python3
"""Demo runner for company pipeline examples."""

from src.cmd.examples.company_pipeline_usage import (
    example_single_source,
    example_multiple_sources, 
    example_custom_source
)


def main() -> int:
    """Run all company pipeline examples."""
    print("Company Ingestion Pipeline Usage Examples")
    print("="*50)
    
    # Run examples (these will show the API but won't actually work without real data)
    example_single_source()
    example_multiple_sources() 
    example_custom_source()
    
    print("\n" + "="*50)
    print("Examples completed!")
    print("Note: These examples show the API usage but won't run successfully")
    print("without real data files and database configuration.")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())