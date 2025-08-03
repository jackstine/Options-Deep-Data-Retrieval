"""NASDAQ screener data loader for CSV files."""

from __future__ import annotations
import csv
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from src.data_sources.models.company import Company


logger = logging.getLogger(__name__)


class ScreenerHeaders:
    """Headers expected in NASDAQ screener CSV files."""
    SYMBOL = "Symbol"
    NAME = "Name"
    LAST_SALE = "Last Sale"
    NET_CHANGE = "Net Change"
    PERCENT_CHANGE = "% Change"
    MARKET_CAP = "Market Cap"
    COUNTRY = "Country"
    IPO_YEAR = "IPO Year"
    VOLUME = "Volume"
    SECTOR = "Sector"
    INDUSTRY = "Industry"


def load_screener_file(file_path: str | Path) -> List[Company]:
    """
    Load NASDAQ screener data from CSV file.
    
    Args:
        file_path: Path to the CSV file (format: nasdaq_screener_MONTH_DAY_YEAR.csv)
        
    Returns:
        List of Company objects with screener data
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is invalid
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Screener file not found: {file_path}")
    
    logger.info(f"Loading NASDAQ screener data from {file_path}")
    
    companies = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            csv_reader = csv.DictReader(f)
            if csv_reader.fieldnames == None:
                raise ValueError(f"data in the csv is not found: {file_path}")
            
            # Validate required headers exist
            required_headers = [
                ScreenerHeaders.SYMBOL,
                ScreenerHeaders.NAME,
                ScreenerHeaders.MARKET_CAP,
                ScreenerHeaders.COUNTRY,
                ScreenerHeaders.SECTOR,
                ScreenerHeaders.INDUSTRY
            ]
            
            missing_headers = [h for h in required_headers if h not in csv_reader.fieldnames]
            if missing_headers:
                raise ValueError(f"Missing required headers: {missing_headers}")
            
            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 for header row
                try:
                    company = _convert_screener_row_to_company(row)
                    if company:
                        companies.append(company)
                except Exception as e:
                    logger.warning(f"Error processing row {row_num}: {e}")
                    continue
        
        logger.info(f"Successfully loaded {len(companies)} companies from screener file")
        return companies
        
    except csv.Error as e:
        raise ValueError(f"Invalid CSV format in file {file_path}: {e}")
    except Exception as e:
        logger.error(f"Error loading screener file {file_path}: {e}")
        raise


def load_screener_files_from_directory(directory_path: str | Path) -> List[Company]:
    """
    Load all NASDAQ screener files from a directory.
    
    Args:
        directory_path: Path to directory containing screener CSV files
        
    Returns:
        List of Company objects from all screener files
    """
    directory_path = Path(directory_path)
    
    if not directory_path.exists():
        raise FileNotFoundError(f"Screener directory not found: {directory_path}")
    
    all_companies = []
    
    # Find all screener files matching the pattern
    screener_files = list(directory_path.glob("nasdaq_screener_*.csv"))
    
    if not screener_files:
        logger.warning(f"No screener files found in {directory_path}")
        return all_companies
    
    logger.info(f"Found {len(screener_files)} screener files")
    
    for file_path in screener_files:
        try:
            companies = load_screener_file(file_path)
            all_companies.extend(companies)
            logger.info(f"Loaded {len(companies)} companies from {file_path.name}")
        except Exception as e:
            logger.error(f"Error loading file {file_path.name}: {e}")
            continue
    
    logger.info(f"Total companies loaded from all screener files: {len(all_companies)}")
    return all_companies


def find_latest_screener_file(directory_path: str | Path) -> Optional[Path]:
    """
    Find the most recent screener file based on filename date.
    
    Args:
        directory_path: Path to directory containing screener CSV files
        
    Returns:
        Path to the latest screener file, or None if no files found
    """
    directory_path = Path(directory_path)
    
    if not directory_path.exists():
        return None
    
    screener_files = list(directory_path.glob("nasdaq_screener_*.csv"))
    
    if not screener_files:
        return None
    
    # Sort files by modification time (most recent first)
    screener_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    return screener_files[0]


def _convert_screener_row_to_company(row: dict) -> Optional[Company]:
    """
    Convert a screener CSV row to Company object.
    
    Args:
        row: Dictionary representing a CSV row
        
    Returns:
        Company object or None if conversion fails
    """
    symbol = row.get(ScreenerHeaders.SYMBOL, "").strip()
    name = row.get(ScreenerHeaders.NAME, "").strip()
    
    # Skip rows with missing essential data
    if not symbol or not name:
        return None
    
    # Parse market cap (remove commas and convert to int)
    market_cap_str = row.get(ScreenerHeaders.MARKET_CAP, "").replace(",", "").strip()
    market_cap = None
    if market_cap_str and market_cap_str != "0.00":
        try:
            market_cap = int(float(market_cap_str))
        except (ValueError, TypeError):
            market_cap = None
    
    # Get other fields with defaults
    country = row.get(ScreenerHeaders.COUNTRY, "").strip() or None
    sector = row.get(ScreenerHeaders.SECTOR, "").strip() or None
    industry = row.get(ScreenerHeaders.INDUSTRY, "").strip() or None
    
    # Determine exchange from symbol characteristics (basic heuristic)
    exchange = "NASDAQ"  # Default to NASDAQ since this is screener data
    
    return Company(
        id=None,
        ticker=symbol,
        company_name=name,
        exchange=exchange,
        sector=sector,
        industry=industry,
        country=country,
        market_cap=market_cap,
        description=None,
        source="NASDAQ_SCREENER"
    )


if __name__ == "__main__":
    # Example usage
    screener_dir = Path(__file__).parent / "data" / "data_screener"
    
    if screener_dir.exists():
        companies = load_screener_files_from_directory(screener_dir)
        print(f"Loaded {len(companies)} companies from screener files")
        
        # Show first few companies
        for company in companies[:5]:
            company.print()
            print("-" * 40)
    else:
        print(f"Screener directory not found: {screener_dir}")