"""
ポートフォリオ分析モジュール。

保有銘柄と市場データを突き合わせて、円換算した評価額・取得額・
含み損益・前日比インパクトなどを計算する。
"""

from typing import Any

# 集計対象外とする銘柄(投資信託・その他枠など、個別株として扱わないもの)
EXCLUDED_TICKERS: set[str] = {
    "S&P500",
    "AI_INDEX",
    "Quantum_Other",
    "OTHER_US",
}

# ドル円レートが取得できなかった場合のフォールバック値
DEFAULT_USD_JPY: float = 150.0


def calculate_portfolio_impact(
    portfolio: dict[str, Any],
    market_data: dict[str, Any],
) -> dict[str, Any]:
    """
    保有銘柄ごとの評価額・含み損益・前日比インパクトを計算する。

    Args:
        portfolio: portfolio.jsonの内容
        market_data: get_market_dataの戻り値

    Returns:
        summary: 資産全体の集計(評価額合計・取得額合計・含み損益・前日比)
        holdings: 銘柄ごとの計算結果一覧(前日比インパクトの大きい順)
    """
    usd_jpy_data = market_data.get("JPY=X", {})
    usd_jpy = usd_jpy_data.get("price", DEFAULT_USD_JPY)

    if "JPY=X" not in market_data:
        print(f"USD/JPYレートが取得できなかったため、デフォルト値({DEFAULT_USD_JPY})を使用します")

    results: list[dict[str, Any]] = []
    total_cost = 0.0
    total_market_value = 0.0
    total_today_impact = 0.0

    for item in portfolio.get("holdings", []):
        ticker = item.get("ticker")

        if not ticker or ticker in EXCLUDED_TICKERS:
            continue

        shares = item.get("shares")
        if not shares or shares <= 0:
            continue

        average_price = item.get("average_price")
        if average_price is None:
            print(f"average_priceが未設定のためスキップ: {ticker}")
            continue

        if ticker not in market_data:
            continue

        data = market_data[ticker]
        if "price" not in data or "change_percent" not in data:
            continue

        current_price = data["price"]
        change = data["change_percent"]

        if item.get("currency") == "JPY":
            cost = shares * average_price
            market_value = shares * current_price
        else:
            cost = shares * average_price * usd_jpy
            market_value = shares * current_price * usd_jpy

        today_impact = market_value * (change / 100)
        unrealized = market_value - cost

        total_cost += cost
        total_market_value += market_value
        total_today_impact += today_impact

        results.append({
            "ticker": ticker,
            "name": item.get("name", ticker),
            "cost_yen": round(cost),
            "market_value_yen": round(market_value),
            "unrealized_yen": round(unrealized),
            "unrealized_percent": round(unrealized / cost * 100, 2) if cost else 0,
            "today_change_percent": change,
            "today_impact_yen": round(today_impact),
            "portfolio_ratio": 0.0,
        })

    results.sort(key=lambda x: x["today_impact_yen"], reverse=True)

    if total_market_value > 0:
        for item in results:
            item["portfolio_ratio"] = round(
                item["market_value_yen"] / total_market_value * 100, 2
            )

    summary = {
        "total_cost_yen": round(total_cost),
        "total_market_value_yen": round(total_market_value),
        "total_unrealized_yen": round(total_market_value - total_cost),
        "total_unrealized_percent": round(
            (total_market_value - total_cost) / total_cost * 100, 2
        ) if total_cost else 0,
        "total_today_impact_yen": round(total_today_impact),
    }

    return {
        "summary": summary,
        "holdings": results,
    }
