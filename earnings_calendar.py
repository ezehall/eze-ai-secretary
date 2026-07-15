"""
決算カレンダー取得モジュール。

Financial Modeling Prep (FMP) APIを使い、保有銘柄の直近決算予定を取得する。
FMP_API_KEYが未設定、またはAPI呼び出しに失敗した場合は空リストを返す
(呼び出し側は常にリストを受け取る前提でよく、型分岐が不要になる)。
"""

import os
from datetime import datetime, timedelta
from typing import Any

import requests

REQUEST_TIMEOUT_SECONDS = 10
DEFAULT_LOOKAHEAD_DAYS = 30

# 決算予定の取得対象外とする銘柄(投資信託・その他枠など)
EXCLUDED_TICKERS: set[str] = {
    "S&P500",
    "AI_INDEX",
    "OTHER_US",
    "Quantum_Other",
}


def get_upcoming_earnings(
    portfolio: dict[str, Any],
    days: int = DEFAULT_LOOKAHEAD_DAYS,
) -> list[dict[str, Any]]:
    """
    保有銘柄のうち、指定日数以内に決算予定がある銘柄を取得する。

    Args:
        portfolio: portfolio.jsonの内容
        days: 何日先までの決算予定を対象とするか

    Returns:
        {"ticker", "date", "epsEstimated", "revenueEstimated"} の辞書のリスト。
        APIキー未設定・取得失敗・想定外レスポンス時は空リストを返す。
    """
    api_key = os.getenv("FMP_API_KEY")

    if not api_key:
        print("FMP_API_KEYが設定されていないため、決算予定の取得をスキップします")
        return []

    tickers = [
        item.get("ticker")
        for item in portfolio.get("holdings", [])
        if item.get("ticker") and item["ticker"] not in EXCLUDED_TICKERS
    ]

    today = datetime.today()
    future = today + timedelta(days=days)

    url = (
        "https://financialmodelingprep.com/stable/earnings-calendar"
        f"?from={today.strftime('%Y-%m-%d')}"
        f"&to={future.strftime('%Y-%m-%d')}"
        f"&apikey={api_key}"
    )

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()

    except Exception as e:
        print(f"決算予定の取得に失敗しました: {e}")
        return []

    if not isinstance(data, list):
        print(f"決算予定APIから想定外の形式のデータが返されました: {type(data)}")
        return []

    return [
        {
            "ticker": item.get("symbol"),
            "date": item.get("date"),
            "epsEstimated": item.get("epsEstimated"),
            "revenueEstimated": item.get("revenueEstimated"),
        }
        for item in data
        if item.get("symbol") in tickers
    ]
