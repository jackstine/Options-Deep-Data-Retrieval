import requests
import src.config.environment as en
from src.data_sources.models.company import Company
import zipfile
import io
import csv

class Headers:
  COMPANY_NAME = "company_name"
  TICKER = "ticker"
  EXCHANGE = "exchange"

def get_companies() -> list[Company]:
  """
  returns the list of companies by making a request to nasdaq
  returns data with the following info.

    "ticker": "ARIA",
    "exchange": "NASDAQ",
    "company_name": "ARIAD Pharmaceuticals Inc."
  """
  return _convert_dict_to_stocks(get_dict_of_stocks())

def get_dict_of_stocks() -> list[dict]|None:
  """
  returns the raw dict of stocks from the Nasdaq company listing api.
  this will read all the data from the API, and will return raw dictionary of the stocks.

    "ticker": "ARIA",
    "exchange": "NASDAQ",
    "company_name": "ARIAD Pharmaceuticals Inc."
  """
  api_key = en.ENVIRONMENT_VARIABLES.get_nasdaq_api_key()
  url = f'https://data.nasdaq.com/api/v3/datatables/QUOTEMEDIA/TICKERS?api_key={api_key}&qopts.export=true'
  response = requests.get(url)
  if response.status_code == 200:
      try:
        content = _validate_response_contents(response.json())
        return _read_download_file(content)
      except Exception as e:
        raise BaseException("get companies did not get the expected response") from e
  else:
      raise BaseException(f'Failed to retrieve nasdaq companies. Status code: {response.status_code}')

def _convert_dict_to_stocks(ds):
  return [Company(ticker=k[Headers.TICKER], company_name=k[Headers.COMPANY_NAME], exchange=k[Headers.EXCHANGE], source="NASDAQ") for k in ds]


def _validate_response_contents(content) -> str:
  """
  returns the content that we design from the nasdaq response.  This should return the URL of the
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
  return content

def _read_download_file(url) -> list[dict]|None:
  """
  this will make a request to get the url zip file and return the data from 
  the single file in the zip file that is a csv file.
  """
  response = requests.get(url)
  if response.status_code == 200:
    return _unzip_company_info_file(response.content)

def _unzip_company_info_file(content) -> list[dict]:
  """
  will take the zip contents, that contains 1 file that is a CSV and return
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
  
def _read_csv_from_file(f) -> list[dict]:
  """
  read_csv_from_file will read the csv file, get the csv file

  should return a list of dicts with all available headers and data
  """
  data = []
  csv_reader = csv.reader(io.TextIOWrapper(f, encoding='utf-8'))
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
  # read_download_file("https://aws-gis-link-pro-us-east-1-datahub.s3.amazonaws.com/export/QUOTEMEDIA/TICKERS/QUOTEMEDIA_TICKERS_6d75499fefd916e54334b292986eafcc.zip?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=ASIAX5EW3SB5MGHOSTNG%2F20240808%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Date=20240808T191558Z&X-Amz-Expires=1800&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEDwaCXVzLWVhc3QtMSJGMEQCIG3kL2yPFvsOS9Vj8U3ZOxFvO1q1QPb3l2nzp%2BI64ZCrAiAYP5L9jGh7lgUodVSVXyC2KGCjNG%2Fpyh81a193%2BgdmLiqMBQg0EAIaDDU0MzYyOTc0MjIwMiIMlrIueSX34Mup9Eb0KukEdFoZPwhvK%2BolGTSTk5fFZ3mzVuFiqUC0hvOqR1iM3REKoPiYYNrBr2FchBLceliGXsshXfQT4VyI%2BaTRCnpmfkjd9nsM7PT2HJTObrryhdcMDip5ltD02rsG7g5AZVwBC1m184W2tvUiCtdnXAWp%2FJnCruAEtSz91eMkoRx3ulisEeGntLT6s3ArdxzXoFEF0bfFR6c29TbcE93bKNzwKm9zm45HB2mtmn5Lggt%2BBueoV1aVbfvQ2zkHWEtB8ByxYYt8gSeMReHIgRTxS4Qk2iwGaZ4hkpi3GJ9RNIK2XVAzjBpTIkvSN2D38SfTAdCxSfu5CR8lmY1iGfzHGXDCdtC7uHzaQ%2F7sW2QlBcPtm5fi0gmlGu1%2BQWRv8P29NNmQ5OOC90GL5ulMEYKePk4w6dXA9qMIE0bjiE2OYDTfUJq%2FFYisUopDYFfFvsv3EUtQ81xTPu8f8g3yrpXHJZxRL4FmVPi1NoSo1BZ6gZpFqCEkO5A4GhQ6jB97SKWCSybOrP8LWZePzg4ouqMNohcBglOwphMBd1FLRG1lI2rt3hqPywx8zXgAk%2FYzQZQfbeHLgl0ID11X6BvrsbaE3NLzlZNsuPULEfLHAmeV5R%2BmaaATgf1ATvkB6trbXOXlog8QixxmDdZztL4ruJqm2wtxuq5g5Y13G47bT4pABazCG1W4un8PZL8K5uvW%2B8oja1kHcOuUpBApioaIgLJ39SYEDRitVBIvHJnh7j1P4BmNDWX6YmZemf9Lrr6oi97USwsWM3C4g1BPkOfmqeWjviblgksIScpcFIQpw67WzNrpziC2V89SYfnAKdQw7rLUtQY6mwGWoSmREOpRlxZkM79IXq4nB8F1%2FRCY6nsT5Pd52ULpnLo3wcpj8m8XQvW9VraH3gWigPqIRwwHdZaN2bJmxSCA0k1faI3RZ5nxHQRcBPTJucithbBSnUrrpxEvkBXT1AiqYinOO6olDxEbL%2B38zskvXUvi7LggZGLNAYJ3vBGfK8%2BcluWUZmMEQWKVv4iZ7ci29YX5C9FDUT8%2FhA%3D%3D&X-Amz-SignedHeaders=host&X-Amz-Signature=27bea85f97c2710c7dc666cca2162f4cf19f355de6e37b3e295dca6b609ca2ab")
  # get_companies()
  data = get_companies()
  for d in data:
    print(d)

