import os
import requests
from datetime import datetime, timedelta


def get_upcoming_earnings(portfolio, days=14):
    """
    保有銘柄の決算予定を取得
    """

    api_key = os.getenv("FMP_API_KEY")

    if not api_key:
        return {
            "error": "FMP_API_KEY が設定されていません"
        }

    earnings_list = []

    # portfolioから自動取得
    tickers = []

    for item in portfolio.get("holdings", []):
        ticker = item.get("ticker")

        # ETFや特殊項目を除外
        if ticker and ticker not in [
            "S&P500",
            "OTHER_US",
            "Quantum_Other"
        ]:
            tickers.append(ticker)


    today = datetime.today()
    future = today + timedelta(days=days)


    for ticker in tickers:

        url = (
            "https://financialmodelingprep.com/api/v3/earning_calendar"
            f"?from={today.strftime('%Y-%m-%d')}"
            f"&to={future.strftime('%Y-%m-%d')}"
            f"&apikey={api_key}"
        )

        try:
            response = requests.get(url)
            data = response.json()

            for item in data:

                if item.get("symbol") == ticker:

                    earnings_list.append(
                        {
                            "ticker": ticker,
                            "date": item.get("date"),
                            "epsEstimated": item.get("epsEstimated"),
                            "revenueEstimated": item.get("revenueEstimated")
                        }
                    )


        except Exception as e:

            earnings_list.append(
                {
                    "ticker": ticker,
                    "error": str(e)
                }
            )


    return earnings_list            response = requests.get(url, timeout=10)
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
