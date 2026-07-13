import os
import requests
from datetime import datetime, timedelta


def get_upcoming_earnings(portfolio, days=30):

    api_key = os.getenv("FMP_API_KEY")

    if not api_key:
        return {
            "error": "FMP_API_KEYがありません"
        }

    results = []

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
        "https://financialmodelingprep.com/stable/earnings-calendar"
        f"?from={today.strftime('%Y-%m-%d')}"
        f"&to={future.strftime('%Y-%m-%d')}"
        f"&apikey={api_key}"
    )


    try:

        response = requests.get(
            url,
            timeout=10
        )

        data = response.json()

        print("取得データ:")
        print(data)


        if isinstance(data, list):

            for item in data:

                if item.get("symbol") in tickers:

                    results.append(
                        {
                            "ticker": item.get("symbol"),
                            "date": item.get("date"),
                            "epsEstimated": item.get("epsEstimated"),
                            "revenueEstimated": item.get("revenueEstimated")
                        }
                    )


    except Exception as e:

        return {
            "error": str(e)
        }


    return results
