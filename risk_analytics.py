"""
リスク分析モジュール(Phase2の積み残し: ボラティリティ・相関分析)。

asset_history.jsonに蓄積された銘柄別の日次値動き(today_change_percent)を
もとに、ボラティリティ(値動きの標準偏差)と銘柄間の相関を計算する。

運用を開始したばかりで蓄積日数が少ない場合、統計的に意味のある結果を
返せない。その場合はavailable=Falseとして「データ蓄積中」であることを
明示し、AIに無理な考察をさせないようにする。
"""

from typing import Any

import pandas as pd

# 統計的にある程度意味のある結果を出すために必要な最低データ点数(営業日数)
MIN_DATA_POINTS = 10

# 相関分析で表示する上位ペア数
TOP_CORRELATION_PAIRS = 3


def _build_returns_table(asset_history: list[dict[str, Any]]) -> pd.DataFrame:
    """asset_historyから、日付×銘柄の値動き(%)の表を組み立てる。"""
    rows: dict[str, dict[str, float]] = {}

    for entry in asset_history:
        date = entry.get("date")

        for holding in entry.get("holdings", []):
            ticker = holding.get("ticker")
            change = holding.get("today_change_percent")

            if ticker is None or change is None:
                continue

            rows.setdefault(date, {})[ticker] = change

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame.from_dict(rows, orient="index").sort_index()


def calculate_volatility(asset_history: list[dict[str, Any]]) -> dict[str, Any]:
    """
    銘柄ごとの日次値動き(%)の標準偏差(簡易ボラティリティ)を計算する。

    Returns:
        {"available", "data_points", "required_data_points", "volatility"}
        available=Falseの場合はデータ蓄積中を意味し、volatilityは空リスト。
    """
    table = _build_returns_table(asset_history)

    if table.empty or len(table) < MIN_DATA_POINTS:
        return {
            "available": False,
            "data_points": len(table),
            "required_data_points": MIN_DATA_POINTS,
            "volatility": [],
        }

    std = table.std().dropna().sort_values(ascending=False)

    return {
        "available": True,
        "data_points": len(table),
        "required_data_points": MIN_DATA_POINTS,
        "volatility": [
            {"ticker": ticker, "volatility_percent": round(float(value), 2)}
            for ticker, value in std.items()
        ],
    }


def calculate_correlation(asset_history: list[dict[str, Any]]) -> dict[str, Any]:
    """
    銘柄間の日次値動き(%)の相関係数を計算し、相関が高いペアの上位を返す。

    Returns:
        {"available", "data_points", "required_data_points", "top_pairs"}
        available=Falseの場合はデータ蓄積中を意味し、top_pairsは空リスト。
    """
    table = _build_returns_table(asset_history)

    if table.empty or len(table) < MIN_DATA_POINTS or table.shape[1] < 2:
        return {
            "available": False,
            "data_points": len(table),
            "required_data_points": MIN_DATA_POINTS,
            "top_pairs": [],
        }

    corr = table.corr()
    tickers = list(corr.columns)

    pairs = []
    for i, ticker_a in enumerate(tickers):
        for ticker_b in tickers[i + 1:]:
            value = corr.loc[ticker_a, ticker_b]

            if pd.isna(value):
                continue

            pairs.append({
                "ticker_a": ticker_a,
                "ticker_b": ticker_b,
                "correlation": round(float(value), 2),
            })

    pairs.sort(key=lambda p: abs(p["correlation"]), reverse=True)

    return {
        "available": True,
        "data_points": len(table),
        "required_data_points": MIN_DATA_POINTS,
        "top_pairs": pairs[:TOP_CORRELATION_PAIRS],
    }
