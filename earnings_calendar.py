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

# 決算日までの残り日数がこの値以下の場合、決算前アラート対象とする
PRE_EARNINGS_ALERT_DAYS = 3

# 決算後、何日前までを「直近の決算結果」として振り返り対象にするか
POST_EARNINGS_LOOKBACK_DAYS = 3

# 決算予定の取得対象外とする銘柄(投資信託・その他枠など)
EXCLUDED_TICKERS: set[str] = {
    "S&P500",
    "AI_INDEX",
    "OTHER_US",
    "Quantum_Other",
}


def _with_alert_fields(entry: dict[str, Any], today: datetime) -> dict[str, Any]:
    """
    決算日までの残り日数(days_until)と、決算前アラート要否(pre_earnings_alert)を
    Python側で確定計算して追加する。

    AIに日数計算を任せると誤差が出ることがあるため、ここで確定させた値を
    レポート生成側にそのまま使わせる。
    """
    entry = dict(entry)
    raw_date = entry.get("date")
    days_until: int | None = None

    if raw_date:
        try:
            earnings_date = datetime.strptime(raw_date, "%Y-%m-%d")
            days_until = (earnings_date.date() - today.date()).days
        except ValueError:
            days_until = None

    entry["days_until"] = days_until
    entry["pre_earnings_alert"] = (
        days_until is not None and 0 <= days_until <= PRE_EARNINGS_ALERT_DAYS
    )

    return entry


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
        {"ticker", "date", "epsEstimated", "revenueEstimated",
         "days_until", "pre_earnings_alert"} の辞書のリスト。
        days_untilは決算日までの残り日数(計算不能な場合はNone)。
        pre_earnings_alertはPRE_EARNINGS_ALERT_DAYS以内に決算がある場合True。
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

    results = [
        {
            "ticker": item.get("symbol"),
            "date": item.get("date"),
            "epsEstimated": item.get("epsEstimated"),
            "revenueEstimated": item.get("revenueEstimated"),
        }
        for item in data
        if item.get("symbol") in tickers
    ]

    return [_with_alert_fields(entry, today) for entry in results]


def get_recent_earnings_results(
    portfolio: dict[str, Any],
    days_back: int = POST_EARNINGS_LOOKBACK_DAYS,
) -> list[dict[str, Any]]:
    """
    直近days_back日以内に決算発表があった保有銘柄について、
    市場予想(EPS)と実績を比較する。

    get_upcoming_earningsと同じFMPのearnings-calendarエンドポイントを
    過去日付の範囲で呼び出すことで実現している(新しいAPI呼び出し先を
    増やしていない)。

    Args:
        portfolio: portfolio.jsonの内容
        days_back: 何日前まで遡って直近決算を確認するか

    Returns:
        {"ticker", "date", "eps_estimated", "eps_actual",
         "eps_surprise_percent", "revenue_estimated", "revenue_actual"} のリスト。
        実績(actual)がまだFMP側に反映されていない銘柄は結果に含めない。
        APIキー未設定・取得失敗時は空リストを返す。
    """
    api_key = os.getenv("FMP_API_KEY")

    if not api_key:
        return []

    tickers = [
        item.get("ticker")
        for item in portfolio.get("holdings", [])
        if item.get("ticker") and item["ticker"] not in EXCLUDED_TICKERS
    ]

    today = datetime.today()
    past = today - timedelta(days=days_back)

    url = (
        "https://financialmodelingprep.com/stable/earnings-calendar"
        f"?from={past.strftime('%Y-%m-%d')}"
        f"&to={today.strftime('%Y-%m-%d')}"
        f"&apikey={api_key}"
    )

    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()

    except Exception as e:
        print(f"直近決算結果の取得に失敗しました: {e}")
        return []

    if not isinstance(data, list):
        print(f"決算結果APIから想定外の形式のデータが返されました: {type(data)}")
        return []

    results: list[dict[str, Any]] = []

    for item in data:
        if item.get("symbol") not in tickers:
            continue

        eps_actual = item.get("epsActual")
        eps_estimated = item.get("epsEstimated")

        # 実績がまだ反映されていない場合はスキップ(直近決算だが未確定)
        if eps_actual is None:
            continue

        surprise_percent = None
        if eps_estimated not in (None, 0):
            surprise_percent = round((eps_actual - eps_estimated) / abs(eps_estimated) * 100, 2)

        results.append({
            "ticker": item.get("symbol"),
            "date": item.get("date"),
            "eps_estimated": eps_estimated,
            "eps_actual": eps_actual,
            "eps_surprise_percent": surprise_percent,
            "revenue_estimated": item.get("revenueEstimated"),
            "revenue_actual": item.get("revenueActual"),
        })

    return results
