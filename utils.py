"""
EZEプロジェクト全体で共有するユーティリティ関数。

各モジュールで重複しがちなエラーログ出力処理をここに集約する。
新しいモジュールを追加する際も、例外処理はここを経由することで
ログ出力の書式を統一する。
"""

import traceback


def log_error(context: str, error: Exception) -> None:
    """
    例外の内容をGitHub Actionsのログに分かりやすく出力する。

    Args:
        context: どの処理で発生したエラーかを示す短い説明
                 (例: "market_data取得失敗")
        error: 発生した例外オブジェクト
    """
    print(f"{context}: {error}")
    print(traceback.format_exc())


def to_market_ticker(ticker: str) -> str:
    """
    portfolio.json上のティッカーを、market_data内で使われるキーに変換する。

    日本株(数字のみのティッカー)は yfinance の仕様上 ".T" を付与した形で
    market_data に格納されるため、参照する側もこの変換を通す必要がある。
    market_data.py側のティッカー生成ロジックと必ず一致させること。

    Args:
        ticker: portfolio.json上のティッカー(例: "7272", "AVGO")

    Returns:
        market_data内のキーとして使われるティッカー(例: "7272.T", "AVGO")
    """
    return f"{ticker}.T" if ticker.isdigit() else ticker
