import os
import requests
import json


def get_upcoming_earnings():

    api_key = os.getenv("FMP_API_KEY")

    if not api_key:
        return {
            "error": "FMP_API_KEY is missing"
        }

    tickers = [
        "NVDA",
        "GOOGL",
        "AVGO",
        "ARM",
        "MU",
        "IONQ",
        "RGTI",
        "ARQQ",
        "OKLO"
    ]

    earnings_list = []

    for ticker in tickers:

        url = (
            "https://financialmodelingprep.com/stable/earnings-calendar?"
            f"symbol={ticker}&apikey={api_key}"
        )

        try:
            response = requests.get(url, timeout=10)
            data = response.json()

            if isinstance(data, list) and len(data) > 0:

                earnings = data[0]

                earnings_list.append({
                    "ticker": ticker,
                    "date": earnings.get("date"),
                    "epsEstimated": earnings.get("epsEstimated"),
                    "revenueEstimated": earnings.get("revenueEstimated")
                })

        except Exception as e:

            earnings_list.append({
                "ticker": ticker,
                "error": str(e)
            })

    return earnings_list
