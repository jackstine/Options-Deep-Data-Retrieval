#!/usr/bin/env python3
"""
NASDAQ Screener Database Sync

Syncs NASDAQ screener data with the database.

Usage:
    python -m src.cmd.nasdaq_screener_sync.main
"""

from __future__ import annotations
import sys

from src.data_sources.nasdaq.database_integration import (
    sync_screener_with_database, 
    print_sync_results
)


def main() -> int:
    """Sync NASDAQ screener data with database."""
    try:
        print("Syncing NASDAQ screener with database...")
        results = sync_screener_with_database()
        print_sync_results(results)
        return 0
        
    except KeyboardInterrupt:
        print("\nCancelled by user")
        return 1
        
    except Exception as e:
        print(f"Sync failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())