import json
import yfinance as yf


def get_market_data():

    # portfolio.jsonから保有銘柄を読み込む
with open("portfolio.json", "r", encoding="utf-8") as f:
    portfolio = json.load(f)

# インデックス・金利・為替（常に取得）
tickers = {
    "S&P500": "^GSPC",
    "NASDAQ": "^IXIC",
    "Dow Jones": "^DJI",
    "VIX": "^VIX",
    "USDJPY": "JPY=X",
    "US10Year": "^TNX",
    "US2Year": "^IRX"
}

# portfolio.jsonに登録されている銘柄を自動追加
for item in portfolio["holdings"]:

    ticker = item["ticker"]

    # 株価取得できないものは除外
    if ticker in [
        "Quantum_Other",
        "OTHER_US",
        "S&P500",
        "AI_INDEX"
    ]:
        continue

    # 日本株
    if ticker.isdigit():
        tickers[item["name"]] = ticker + ".T"
    else:
        tickers[item["name"]] = ticker
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
