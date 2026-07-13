import yfinance as yf


def get_market_data():

    tickers = {
    "S&P500": "^GSPC",
    "NASDAQ": "^IXIC",
    "Dow Jones": "^DJI",
    "VIX": "^VIX",

    "USDJPY": "JPY=X",

    # 金利関連
    "US10Year": "^TNX",
    "US2Year": "^IRX",

        # AI・半導体
    "NVIDIA": "NVDA",
    "Alphabet": "GOOGL",
    "Alphabet C": "GOOG",
    "Broadcom": "AVGO",
    "ARM": "ARM",
    "Micron": "MU",
    "TSMC": "TSM",
    "Palantir": "PLTR",

    # 量子関連
    "IonQ": "IONQ",
    "IONL": "IONL",
    "Rigetti": "RGTI",
    "Arqit": "ARQQ",
    "Quantum Computing": "QUBT",
    "Quantum": "QMCO",

    # ETF
    "SOXL": "SOXL",
    "SPCX": "SPCX",

    # 日本株
    "Yamaha": "7272.T",

    # 次世代エネルギー
    "Oklo": "OKLO"
    }

    result = {}

    for name, ticker in tickers.items():

        try:
            data = yf.Ticker(ticker).history(period="2d")

            today = data["Close"].iloc[-1]
            yesterday = data["Close"].iloc[-2]

            change = ((today - yesterday) / yesterday) * 100

            result[ticker] = {
                "name": name,
                "price": round(float(today), 2),
                "change_percent": round(float(change), 2)
            }

        except Exception as e:
            result[ticker] = {
                "name": name,
                "error": str(e)
            }

    return result
