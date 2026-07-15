"""
売買履歴反映モジュール(Phase3)。

trade_history.jsonに登録された未反映の売買(buy/sell)をportfolio.jsonへ
反映し、保有株数・平均取得単価を自動計算する。

使い方(スマホのGitHubアプリ想定):
trade_history.jsonに以下の形式でオブジェクトを1件追加してコミットするだけでよい。

{
    "ticker": "NVDA",
    "name": "NVIDIA",
    "action": "buy",
    "shares": 5,
    "price": 185.2,
    "currency": "USD",
    "account": "NISA",
    "category": "AI半導体"
}

次回の自動実行時にportfolio.jsonへ反映され、このオブジェクトには
applied: true が自動的に付与される(二重反映防止のため、付与後は
手動で編集・削除しないこと)。

sell(売却)の場合はshares・priceのみ必須(name/currency/account/category は
既存の保有銘柄から引き継ぐため不要)。
"""

import json
from typing import Any

TRADE_HISTORY_PATH = "trade_history.json"

VALID_ACTIONS = {"buy", "sell"}

# 平均取得単価の丸め桁数(portfolio.json内の既存の値と桁数を合わせている)
AVERAGE_PRICE_DECIMALS = 4


def load_trade_history(path: str = TRADE_HISTORY_PATH) -> list[dict[str, Any]]:
    """
    売買履歴を読み込む。

    ファイルが存在しない、または内容が壊れている場合は空リストを返す
    (この機能を導入していない状態、または導入直後でもクラッシュしない)。
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    if not isinstance(data, list):
        return []

    return data


def _find_holding(portfolio: dict[str, Any], ticker: str) -> dict[str, Any] | None:
    """portfolio内から指定ティッカーの保有銘柄を探す(見つかればその実体への参照を返す)。"""
    for item in portfolio.get("holdings", []):
        if item.get("ticker") == ticker:
            return item
    return None


def _apply_buy(
    holding: dict[str, Any] | None,
    trade: dict[str, Any],
    portfolio: dict[str, Any],
) -> None:
    """
    買付・追加購入を反映する。

    既存銘柄であれば加重平均法で平均取得単価を再計算し、
    未保有の新規銘柄であればholdingsへ新しいエントリを追加する。
    """
    shares = trade["shares"]
    price = trade["price"]

    if holding is None:
        portfolio.setdefault("holdings", []).append({
            "ticker": trade["ticker"],
            "name": trade.get("name", trade["ticker"]),
            "shares": shares,
            "average_price": round(price, AVERAGE_PRICE_DECIMALS),
            "currency": trade.get("currency", "USD"),
            "account": trade.get("account", "特定"),
            "category": trade.get("category", "その他"),
        })
        return

    old_shares = holding.get("shares", 0)
    old_avg = holding.get("average_price", 0)

    new_shares = old_shares + shares
    new_avg = (old_shares * old_avg + shares * price) / new_shares

    holding["shares"] = new_shares
    holding["average_price"] = round(new_avg, AVERAGE_PRICE_DECIMALS)


def _apply_sell(holding: dict[str, Any] | None, trade: dict[str, Any]) -> str | None:
    """
    売却を反映する。平均取得単価は変更せず、株数のみ減らす。

    Returns:
        処理できなかった場合のエラーメッセージ。問題なければNone。
    """
    ticker = trade["ticker"]

    if holding is None:
        return f"{ticker}: 保有していない銘柄の売却が指定されました"

    remaining = holding.get("shares", 0) - trade["shares"]

    if remaining < 0:
        return (
            f"{ticker}: 保有株数({holding.get('shares', 0)})を超える"
            f"売却株数({trade['shares']})が指定されました"
        )

    holding["shares"] = remaining
    return None


def apply_trades(
    portfolio: dict[str, Any],
    trades: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[str], bool]:
    """
    未反映(applied=falseまたは未設定)の売買をportfolioへ反映する。

    Args:
        portfolio: portfolio.jsonの内容。この関数内で直接書き換える。
        trades: trade_history.jsonの内容。

    Returns:
        (更新後のportfolio, 更新後のtrades, エラーメッセージのリスト, 変更の有無)
        エラーが起きたトレードはapplied化されず、内容を修正すれば次回以降に
        再び反映を試みる。
    """
    errors: list[str] = []
    changed = False

    for trade in trades:
        if trade.get("applied"):
            continue

        try:
            ticker = trade["ticker"]
            action = trade.get("action")
            shares = trade.get("shares")
            price = trade.get("price")

            if action not in VALID_ACTIONS:
                errors.append(f"{ticker}: actionは'buy'または'sell'のみ指定できます(値: {action})")
                continue

            if not isinstance(shares, (int, float)) or shares <= 0:
                errors.append(f"{ticker}: sharesは正の数値である必要があります(値: {shares})")
                continue

            if not isinstance(price, (int, float)) or price <= 0:
                errors.append(f"{ticker}: priceは正の数値である必要があります(値: {price})")
                continue

            holding = _find_holding(portfolio, ticker)

            if action == "buy":
                _apply_buy(holding, trade, portfolio)
            else:
                error = _apply_sell(holding, trade)
                if error:
                    errors.append(error)
                    continue

            trade["applied"] = True
            changed = True

        except KeyError as e:
            errors.append(f"必須項目が不足しています(不足キー: {e})")
        except Exception as e:
            errors.append(f"{trade.get('ticker', '不明な銘柄')}: 処理中にエラーが発生しました({e})")

    return portfolio, trades, errors, changed
