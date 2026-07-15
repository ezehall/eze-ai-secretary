"""
資産推移ログモジュール(基盤系)。

日々のポートフォリオ評価額・含み損益・銘柄別の値動きをasset_history.jsonに
追記して蓄積する。ボラティリティ分析・相関分析・将来の資産推移グラフの
基礎データとなる。

注意: GitHub Actionsのランナーは実行のたびに使い捨てられるため、
このファイルへの変更はワークフロー側でコミット・pushしない限り
毎回消えてしまう。daily.ymlに「変更をコミットする」ステップが
必要(README/ワークフロー参照)。
"""

import json
from datetime import datetime
from typing import Any

import pytz

ASSET_HISTORY_PATH = "asset_history.json"
JAPAN_TZ = pytz.timezone("Asia/Tokyo")


def _today_jst() -> str:
    """日本時間における「今日」の日付文字列(YYYY-MM-DD)を返す。"""
    return datetime.now(JAPAN_TZ).strftime("%Y-%m-%d")


def load_asset_history(path: str = ASSET_HISTORY_PATH) -> list[dict[str, Any]]:
    """
    資産推移ログを読み込む。

    ファイルが存在しない、または内容が壊れている場合は空リストを返す
    (導入直後や手動編集ミスでクラッシュしないようにする)。
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    if not isinstance(data, list):
        return []

    return data


def append_daily_snapshot(
    portfolio_impact: dict[str, Any],
    path: str = ASSET_HISTORY_PATH,
) -> list[dict[str, Any]]:
    """
    本日分の評価額・含み損益・銘柄別の値動きをasset_history.jsonに追記する。

    同じ日付のエントリが既に存在する場合は上書きする
    (1日に複数回実行しても重複しないようにするため)。

    Args:
        portfolio_impact: calculate_portfolio_impactの戻り値
        path: 保存先ファイルパス

    Returns:
        更新後の資産推移ログ全体(日付昇順)
    """
    history = load_asset_history(path)
    today = _today_jst()

    summary = portfolio_impact.get("summary", {})

    snapshot = {
        "date": today,
        "total_market_value_yen": summary.get("total_market_value_yen"),
        "total_cost_yen": summary.get("total_cost_yen"),
        "total_unrealized_yen": summary.get("total_unrealized_yen"),
        "total_unrealized_percent": summary.get("total_unrealized_percent"),
        "holdings": [
            {
                "ticker": holding.get("ticker"),
                "market_value_yen": holding.get("market_value_yen"),
                "today_change_percent": holding.get("today_change_percent"),
            }
            for holding in portfolio_impact.get("holdings", [])
        ],
    }

    history = [entry for entry in history if entry.get("date") != today]
    history.append(snapshot)
    history.sort(key=lambda entry: entry.get("date", ""))

    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    return history
