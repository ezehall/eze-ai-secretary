"""
バリュエーションデータ取得モジュール(Phase2)。

Financial Modeling Prep (FMP) APIのStock Quoteエンドポイントを使い、
保有銘柄のPER(株価収益率)を取得する。
決算カレンダー(earnings_calendar.py)と同じFMP_API_KEYを利用する。

注意: 当初はTTM Ratios API(/stable/ratios-ttm)を使う設計だったが、
これは有料プラン限定のエンドポイントであり、無料プランでは
402 Payment Requiredエラーになることが判明した。
そのため無料プランでも利用できるStock Quote API(/stable/quote)に
切り替えている。このエンドポイントはPERのみを含み、PBR・PEG・PSRは
含まれないため、それらの項目は常にNoneになる。

割高・割安の最終判断はAI側の定性判断に委ねるが、根拠となる数値は
ここで確定させ、AIに数値を推測させないようにする。
"""

import os
import time
from typing import Any

import requests

REQUEST_TIMEOUT_SECONDS = 10

# 銘柄間のリクエスト間隔。FMP側への連続アクセスを避けるための小休止。
REQUEST_INTERVAL_SECONDS = 0.3

# バリュエーションデータの取得対象外とする銘柄
# (投資信託・ETF・レバレッジ商品など、PER等の指標が意味を持たないもの)
EXCLUDED_TICKERS: set[str] = {
    "S&P500",
    "AI_INDEX",
    "OTHER_US",
    "Quantum_Other",
    "IONL",
    "SPCX",
}


def _fetch_quote(ticker: str, api_key: str) -> dict[str, Any] | None:
    """
    1銘柄分の株価クオートを取得し、PERを取り出す。

    FMPのレスポンス上のPERの項目名はドキュメント上「pe」だが、
    バージョンによって表記が異なる可能性があるため、複数の
    候補キーを順に確認する。

    Returns:
        評価指標の辞書。取得できなかった場合はNone。
    """
    url = (
        "https://financialmodelingprep.com/stable/quote"
        f"?symbol={ticker}&apikey={api_key}"
    )

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()

    except Exception as e:
        print(f"評価指標の取得に失敗: {ticker} / {e}")
        return None

    if not isinstance(data, list) or not data:
        print(f"評価指標データが空、または想定外の形式: {ticker}")
        return None

    entry = data[0]

    pe_ratio = entry.get("pe")
    if pe_ratio is None:
        pe_ratio = entry.get("peRatio")

    return {
        "ticker": ticker,
        "pe_ratio": pe_ratio,
        "eps": entry.get("eps"),
        # Stock Quote APIには含まれないため常にNone。
        # 将来的に有料プランへ移行する場合はratios-ttm等に切り替えて埋める。
        "pb_ratio": None,
        "peg_ratio": None,
        "ps_ratio": None,
    }


def get_valuation_data(portfolio: dict[str, Any]) -> list[dict[str, Any]]:
    """
    保有銘柄のPERを取得する(無料プランの制約上、PBR・PEG・PSRは常にNone)。

    Args:
        portfolio: portfolio.jsonの内容

    Returns:
        {"ticker", "pe_ratio", "eps", "pb_ratio", "peg_ratio", "ps_ratio"} の
        辞書のリスト。値が取得できなかった項目はNoneになる。
        APIキー未設定時は空リストを返す。個別銘柄の取得失敗は
        その銘柄をスキップするだけで、全体は失敗させない。
    """
    api_key = os.getenv("FMP_API_KEY")

    if not api_key:
        print("FMP_API_KEYが設定されていないため、評価指標の取得をスキップします")
        return []

    tickers = [
        item.get("ticker")
        for item in portfolio.get("holdings", [])
        if item.get("ticker")
        and item["ticker"] not in EXCLUDED_TICKERS
        and item.get("shares", 0) > 0
    ]

    results: list[dict[str, Any]] = []

    for ticker in tickers:
        data = _fetch_quote(ticker, api_key)

        if data is not None:
            results.append(data)

        time.sleep(REQUEST_INTERVAL_SECONDS)

    return results
