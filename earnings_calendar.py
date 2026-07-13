import os
import requests
from datetime import datetime, timedelta


def get_upcoming_earnings(portfolio, days=14):

    api_key = os.getenv("FMP_API_KEY")

    if not api_key:
        return {
            "error": "FMP_API_KEY が設定されていません"
        }

    earnings_list = []

    tickers = []

    for item in portfolio.get("holdings", []):

        ticker = item.get("ticker")

        if ticker and ticker not in [
            "S&P500",
            "OTHER_US",
            "Quantum_Other"
        ]:
            tickers.append(ticker)


    today = datetime.today()
    future = today + timedelta(days=days)


    url = (
        "https://financialmodelingprep.com/api/v3/earning_calendar"
        f"?from={today.strftime('%Y-%m-%d')}"
        f"&to={future.strftime('%Y-%m-%d')}"
        f"&apikey={api_key}"
    )


    try:

        response = requests.get(url, timeout=10)
        data = response.json()

        print("FMP RESPONSE:")
        print(data)
        
        if not isinstance(data, list):
            return {
                "error": data
            }


        for item in data:

            symbol = item.get("symbol")

            if symbol in tickers:

                earnings_list.append(
                    {
                        "ticker": symbol,
                        "date": item.get("date"),
                        "epsEstimated": item.get("epsEstimated"),
                        "revenueEstimated": item.get("revenueEstimated")
                    }
                )


    except Exception as e:

        return {
            "error": str(e)
        }


    return earnings_list
