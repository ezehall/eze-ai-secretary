"""
市場データ取得モジュール。

主要指数(S&P500, NASDAQ, Dow, VIX, ドル円, 米10年債, 米13週国債)と、
portfolio.jsonに登録されている保有銘柄の株価をyfinance経由で取得する。

保有銘柄はportfolio.jsonから自動的に読み込まれるため、
銘柄を追加する際はportfolio.jsonを更新するだけでよく、
このファイルを直接編集する必要はない。
"""

import math
import time
from typing import Any

import yfinance as yf

from utils import to_market_ticker

# 常に取得する市場全体の指標
#
# 注: "US2Year"ではなく"US3Month"としている。
# ^IRXはYahoo Finance上「13週(13 WEEK TREASURY BILL)」であり、2年債ではない。
# 2年債に相当する信頼できる単一ティッカーがYahoo Finance上に無いため、
# 実際に取得している短期金利の実態に合わせてラベルを訂正している。
BASE_TICKERS: dict[str, str] = {
    "S&P500": "^GSPC",
    "NASDAQ": "^IXIC",
    "Dow Jones": "^DJI",
    "VIX": "^VIX",
    "USDJPY": "JPY=X",
    "US10Year": "^TNX",
    "US3Month": "^IRX",
}

# 株価データの取得対象外とする銘柄(投資信託・その他枠など、yfinanceで取得できないもの)
EXCLUDED_TICKERS: set[str] = {
    "Quantum_Other",
    "OTHER_US",
    "S&P500",
    "AI_INDEX",
}

# yfinance/Yahoo側の一時的な取得失敗(NaN応答・データ不足を含む)に対するリトライ設定
MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 5

# 銘柄数が多いため、連続リクエストでYahoo側のレート制限を受けないよう
# 1銘柄ごとに小休止を入れる
REQUEST_INTERVAL_SECONDS = 0.5

# 取得期間。市場休場日や一時的な欠損があっても直近2営業日分の終値を
# 拾えるよう、必要な2日分より広めに取得する
HISTORY_PERIOD = "5d"


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

        tickers[item["name"]] = to_market_ticker(ticker)

    return tickers


def _parse_price_history(ticker: str, data: Any) -> dict[str, float] | None:
    """
    yfinanceのhistory()結果から直近2営業日分の終値を取り出し、
    価格と前日比を計算する。

    データ不足・NaN・0除算などの不正なケースはすべてNoneとして扱い、
    呼び出し側でリトライまたはスキップの判断ができるようにする。
    """
    if data is None or len(data) < 2:
        print(f"データ不足: {ticker}")
        return None

    today_price = float(data["Close"].iloc[-1])
    yesterday_price = float(data["Close"].iloc[-2])

    if math.isnan(today_price) or math.isnan(yesterday_price) or yesterday_price == 0:
        print(f"価格データが不正(NaNまたは0): {ticker}")
        return None

    change_percent = ((today_price - yesterday_price) / yesterday_price) * 100

    if math.isnan(change_percent):
        print(f"前日比の計算に失敗(NaN): {ticker}")
        return None

    return {
        "price": round(today_price, 2),
        "change_percent": round(change_percent, 2),
    }


def _fetch_ticker_data(ticker: str) -> dict[str, float] | None:
    """
    1銘柄分の価格データをyfinanceから取得する。

    通信エラーだけでなく、NaN・データ不足で返ってきた場合も
    Yahoo側の一時的な問題である可能性が高いため、同様にリトライする。

    Returns:
        {"price": float, "change_percent": float} または取得不能ならNone
    """
    last_error: Exception | None = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            data = yf.Ticker(ticker).history(period=HISTORY_PERIOD)
            result = _parse_price_history(ticker, data)

            if result is not None:
                return result

        except Exception as e:
            last_error = e

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY_SECONDS)

    if last_error is not None:
        print(f"取得失敗: {ticker} / {last_error}")

    return None


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
        price_data = _fetch_ticker_data(ticker)

        if price_data is not None:
            result[ticker] = {
                "name": name,
                **price_data,
            }

        # Yahoo側への連続アクセスを避けるための小休止
        time.sleep(REQUEST_INTERVAL_SECONDS)

    return result
