"""
市場データ取得モジュール。

主要指数(S&P500, NASDAQ, Dow, VIX, ドル円, 米10年債, 米2年債)と、
portfolio.jsonに登録されている保有銘柄の株価をyfinance経由で取得する。

保有銘柄はportfolio.jsonから自動的に読み込まれるため、
銘柄を追加する際はportfolio.jsonを更新するだけでよく、
このファイルを直接編集する必要はない。
"""

from typing import Any

import yfinance as yf

# 常に取得する市場全体の指標
BASE_TICKERS: dict[str, str] = {
    "S&P500": "^GSPC",
    "NASDAQ": "^IXIC",
    "Dow Jones": "^DJI",
    "VIX": "^VIX",
    "USDJPY": "JPY=X",
    "US10Year": "^TNX",
    "US2Year": "^IRX",
}

# 株価データの取得対象外とする銘柄(投資信託・その他枠など、yfinanceで取得できないもの)
EXCLUDED_TICKERS: set[str] = {
    "Quantum_Other",
    "OTHER_US",
    "S&P500",
    "AI_INDEX",
}


def _build_ticker_map(portfolio: dict[str, Any]) -> dict[str, str]:
    """
    portfolio.jsonの保有銘柄からyfinance用のティッカーマップを組み立てる。

    日本株(数字のみのティッカー)は末尾に".T"を付与する。

    Args:
        portfolio: portfolio.jsonの内容

    Returns:
        表示名をキー、yfinance用ティッカーを値とする辞書
    """
    tickers = dict(BASE_TICKERS)

    for item in portfolio.get("holdings", []):
        ticker = item.get("ticker")

        if not ticker or ticker in EXCLUDED_TICKERS:
            continue

        if ticker.isdigit():
            tickers[item["name"]] = f"{ticker}.T"
        else:
            tickers[item["name"]] = ticker

    return tickers


def get_market_data(portfolio: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """
    市場全体の指標と、portfolioに含まれる保有銘柄の株価データを取得する。

    Args:
        portfolio: portfolio.jsonの内容(main.py側で読み込んだものを渡す)

    Returns:
        ティッカーをキーとした辞書。各値は以下を含む。
            name: 表示名
            price: 現在値
            change_percent: 前日比(%)
        個別銘柄の取得に失敗した場合、その銘柄は結果に含まれない
        (関数全体は失敗させない)。
    """
    tickers = _build_ticker_map(portfolio)

    result: dict[str, dict[str, Any]] = {}

    for name, ticker in tickers.items():
        try:
            data = yf.Ticker(ticker).history(period="2d")

            if len(data) < 2:
                print(f"データ不足: {ticker}")
                continue

            today_price = data["Close"].iloc[-1]
            yesterday_price = data["Close"].iloc[-2]
            change_percent = ((today_price - yesterday_price) / yesterday_price) * 100

            result[ticker] = {
                "name": name,
                "price": round(float(today_price), 2),
                "change_percent": round(float(change_percent), 2),
            }

        except Exception as e:
            print(f"取得失敗: {ticker} / {e}")
            continue

    return result
