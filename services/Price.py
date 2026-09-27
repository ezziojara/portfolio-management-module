"""
Price provider.

It exposes a single function, `get_current_price(symbol) -> float`, which returns
the latest available closing price for a stock.

- By default it uses mock responses (Alpha Vantage TIME_SERIES_DAILY format), so
  the project can run without network access or credentials.
- If the ALPHAVANTAGE_API_KEY environment variable is set, it queries the real API.
  (Note: the free tier of this API allows only about one request per second.)

"The latest available" price is taken from the most recent date in the series.
"""
import os

import requests

ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"

mock_response_META = {'Meta Data': {'1. Information': 'Daily Prices (open, high, low, close) and Volumes', '2. Symbol': 'META', '3. Last Refreshed': '2026-09-25', '4. Output Size': 'Compact', '5. Time Zone': 'US/Eastern'}, 'Time Series (Daily)': {'2026-09-25': {'1. open': '768.8450', '2. high': '769.5700', '3. low': '746.5405', '4. close': 751.6600, '5. volume': '25826729'}}}
mock_response_AAPL = { 'Meta Data': { '1. Information': 'Daily Prices (open, high, low, close) and Volumes', '2. Symbol': 'AAPL', '3. Last Refreshed': '2026-09-25', '4. Output Size': 'Compact', '5. Time Zone': 'US/Eastern' }, 'Time Series (Daily)': { '2026-09-25': { '1. open': '336.0400', '2. high': '341.6700', '3. low': '334.5300', '4. close': 341.0700, '5. volume': '30002507' }}}


MOCK_RESPONSES = {
    "META": mock_response_META,
    "AAPL": mock_response_AAPL,
}


def fetch_daily_series(symbol: str) -> dict:
    """Returns the raw TIME_SERIES_DAILY response for `symbol`."""
    api_key = os.environ.get("ALPHAVANTAGE_API_KEY")
    if not api_key:
        if symbol not in MOCK_RESPONSES:
            raise ValueError(f"No mock data available for {symbol}")
        return MOCK_RESPONSES[symbol]

    response = requests.get(
        ALPHA_VANTAGE_URL,
        params={"function": "TIME_SERIES_DAILY", "symbol": symbol, "apikey": api_key},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    if "Time Series (Daily)" not in data:
        # Alpha Vantage may return HTTP 200 with an error or rate-limit message in the body.
        raise RuntimeError(f"Unexpected response for {symbol}: {data}")
    return data


def get_current_price(symbol: str) -> float:
    """Latest available closing price for `symbol`."""
    series = fetch_daily_series(symbol)["Time Series (Daily)"]
    last_date = max(series)  # ISO dates (YYYY-MM-DD) sort correctly as strings
    return float(series[last_date]["4. close"])
