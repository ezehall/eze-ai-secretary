import yfinance as yf


def get_market_data():

    tickers = {
        "S&P500": "^GSPC",
        "NASDAQ": "^IXIC",
        "Dow Jones": "^DJI",
        "VIX": "^VIX",
        "USDJPY": "JPY=X",
        "NVIDIA": "NVDA",
        "IonQ": "IONQ",
        "Rigetti": "RGTI",
        "Arqit": "ARQQ",
        "Alphabet": "GOOGL",
        "Broadcom": "AVGO",
        "ARM": "ARM",
        "Micron": "MU",
        "Oklo": "OKLO"
    }

    result = {}

    for name, ticker in tickers.items():

        try:
            data = yf.Ticker(ticker).history(period="2d")

            today = data["Close"].iloc[-1]
            yesterday = data["Close"].iloc[-2]

            change = ((today - yesterday) / yesterday) * 100

            result[name] = {
                "price": round(float(today), 2),
                "change_percent": round(float(change), 2)
            }

        except Exception as e:
            result[name] = {
                "error": str(e)
            }

    return result
