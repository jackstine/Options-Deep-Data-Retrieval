import csv
import io
import zipfile
from typing import Any

import requests

from src.config.configuration import CONFIG
from src.data_sources.base.company_data_source import CompanyDataSource
from src.data_sources.models.company import Company


class Headers:
    COMPANY_NAME = "company_name"
    TICKER = "ticker"
    EXCHANGE = "exchange"


class NasdaqCompanySource(CompanyDataSource):
    """NASDAQ company data source using API."""

    @property
    def name(self) -> str:
        """Name of the data source."""
        return "NASDAQ API"

    def get_companies(self) -> list[Company]:
        """Returns the list of companies by making a request to NASDAQ API.
        Returns data with the following info:
          "ticker": "ARIA",
          "exchange": "NASDAQ",
          "company_name": "ARIAD Pharmaceuticals Inc."
        """
        dict_data = self._get_dict_of_stocks()
        if dict_data is None:
            return []
        return _convert_dict_to_stocks(dict_data)

    def is_available(self) -> bool:
        """Check if NASDAQ API is available."""
        try:
            api_key = CONFIG.get_nasdaq_api_key()
            return api_key is not None
        except Exception:
            return False

    def _get_dict_of_stocks(self) -> list[dict] | None:
        """Returns the raw dict of stocks from the NASDAQ company listing API.
        This will read all the data from the API, and will return raw dictionary of the stocks.
          "ticker": "ARIA",
          "exchange": "NASDAQ",
          "company_name": "ARIAD Pharmaceuticals Inc."
        """
        api_key = CONFIG.get_nasdaq_api_key()
        url = f"https://data.nasdaq.com/api/v3/datatables/QUOTEMEDIA/TICKERS?api_key={api_key}&qopts.export=true"
        response = requests.get(url)
        if response.status_code == 200:
            try:
                content = _validate_response_contents(response.json())
                return _read_download_file(content)
            except Exception as e:
                raise BaseException(
                    "get companies did not get the expected response"
                ) from e
        else:
            raise BaseException(
                f"Failed to retrieve nasdaq companies. Status code: {response.status_code}"
            )


# Backward compatibility functions
def get_companies() -> list[Company]:
    """DEPRECATED: Use NasdaqCompanySource class instead.

    Returns the list of companies by making a request to NASDAQ API.
    Returns data with the following info:
      "ticker": "ARIA",
      "exchange": "NASDAQ",
      "company_name": "ARIAD Pharmaceuticals Inc."
    """
    source = NasdaqCompanySource()
    return source.get_companies()


def get_dict_of_stocks() -> list[dict] | None:
    """DEPRECATED: Use NasdaqCompanySource._get_dict_of_stocks() instead.

    Returns the raw dict of stocks from the NASDAQ company listing API.
    This will read all the data from the API, and will return raw dictionary of the stocks.
      "ticker": "ARIA",
      "exchange": "NASDAQ",
      "company_name": "ARIAD Pharmaceuticals Inc."
    """
    source = NasdaqCompanySource()
    return source._get_dict_of_stocks()


def _convert_dict_to_stocks(ds: list[dict]) -> list[Company]:
    """Convert dictionary data to Company objects."""
    from src.data_sources.models.ticker import Ticker

    companies = []
    for k in ds:
        ticker = Ticker(symbol=k[Headers.TICKER], company_id=None)
        company = Company(
            company_name=k[Headers.COMPANY_NAME],
            exchange=k[Headers.EXCHANGE],
            ticker=ticker,
            source="NASDAQ",
        )
        companies.append(company)
    return companies


def _validate_response_contents(content: dict) -> str:
    """Returns the content that we design from the nasdaq response.  This should return the URL of the
    signed bucket file
    """
    DBD = "datatable_bulk_download"
    F = "file"
    L = "link"
    if DBD in content:
        content = content[DBD]
        if F in content:
            content = content[F]
            if L in content:
                content = content[L]
            else:
                raise BaseException("nasdaq response does not have {L}")
        else:
            raise BaseException("nasdaq response does not have {F}")
    else:
        raise BaseException("nasdaq response does not have {DBD}")
    return str(content)


def _read_download_file(url: str) -> list[dict] | None:
    """This will make a request to get the url zip file and return the data from
    the single file in the zip file that is a csv file.
    """
    response = requests.get(url)
    if response.status_code == 200:
        return _unzip_company_info_file(response.content)
    return None


def _unzip_company_info_file(content: bytes) -> list[dict]:
    """Will take the zip contents, that contains 1 file that is a CSV and return
    data from it, if the contents of the csv file contains the headers
    then the returned data is a list of dictionaries of the data.
    """
    with zipfile.ZipFile(io.BytesIO(content)) as z:
        file_names = z.namelist()
        # there should only be one file name in the file
        assert len(file_names) == 1
        csv_filename = file_names[0]
        with z.open(csv_filename) as f:
            data = _read_csv_from_file(f)
            return data


def _read_csv_from_file(f: Any) -> list[dict]:
    """read_csv_from_file will read the csv file, get the csv file

    should return a list of dicts with all available headers and data
    """
    data = []
    csv_reader = csv.reader(io.TextIOWrapper(f, encoding="utf-8"))
    headers = list()
    for i, row in enumerate(csv_reader):
        if i == 0:
            headers = row
            assert Headers.COMPANY_NAME in headers
            assert Headers.TICKER in headers
            assert Headers.EXCHANGE in headers
        else:
            d = dict()
            for j in range(len(headers)):
                if j < len(row):
                    d[headers[j]] = row[j]
                else:
                    d[headers[j]] = ""  # Handle missing values
            data.append(d)
    return data


if __name__ == "__main__":
    # Example usage with new class
    source = NasdaqCompanySource()
    if source.is_available():
        print(f"Using data source: {source.name}")
        companies = source.get_companies()
        print(f"Retrieved {len(companies)} companies")
        for company in companies[:5]:  # Show first 5
            company.print()
            print("-" * 40)
    else:
        print("NASDAQ API source is not available")
