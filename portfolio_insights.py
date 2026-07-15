"""
ポートフォリオ洞察モジュール(Phase2)。

portfolio.jsonとportfolio_analysisの計算結果をもとに、
テーマ別の資産配分と集中投資リスクをPython側で確定的に計算する。

割高・割安分析や長期成長性評価のような定性的な判断はAI(main.py側の
プロンプト)に委ねるが、比率や集中度のような数値はここで確定させ、
AIに推測させないようにすることでレポートの数値の正確性を担保する。
"""

from typing import Any

# 投資家プロフィールの4大テーマ。portfolio.json上の"category"文字列に
# これらのキーワードが含まれるかどうかで分類する。
# 複数のキーワードに一致する場合は、辞書の並び順で最初に一致したテーマを採用する
# (例: "AI半導体"は"AI"に分類され、"半導体"には二重計上しない)。
THEME_KEYWORDS: dict[str, list[str]] = {
    "AI": ["AI", "ai"],
    "半導体": ["半導体"],
    "量子コンピュータ": ["量子"],
    "次世代エネルギー": ["エネルギー"],
}

OTHER_THEME = "その他"

# 集中投資リスクとみなす閾値(資産全体に対する比率、%)
SINGLE_HOLDING_THRESHOLD_PERCENT = 15.0
SINGLE_THEME_THRESHOLD_PERCENT = 40.0


def _classify_theme(category: str) -> str:
    """portfolio.json上のcategory文字列を4大テーマのいずれかに分類する。"""
    for theme, keywords in THEME_KEYWORDS.items():
        if any(keyword in category for keyword in keywords):
            return theme

    return OTHER_THEME


def calculate_theme_allocation(
    portfolio: dict[str, Any],
    portfolio_impact: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    保有銘柄をテーマ別(AI/半導体/量子コンピュータ/次世代エネルギー/その他)に
    分類し、評価額ベースの配分比率を計算する。

    Args:
        portfolio: portfolio.jsonの内容(各銘柄のcategoryを参照するため)
        portfolio_impact: calculate_portfolio_impactの戻り値
                           (評価額market_value_yenを参照するため)

    Returns:
        {"theme", "value_yen", "ratio_percent", "tickers"} の辞書のリスト。
        比率が大きい順に並んでいる。評価額データが無い場合は空リスト。
    """
    category_by_ticker: dict[str, str] = {
        item["ticker"]: item.get("category", "")
        for item in portfolio.get("holdings", [])
    }

    totals: dict[str, float] = {}
    tickers_by_theme: dict[str, list[str]] = {}

    for holding in portfolio_impact.get("holdings", []):
        ticker = holding.get("ticker")
        category = category_by_ticker.get(ticker, "")
        theme = _classify_theme(category)

        totals[theme] = totals.get(theme, 0.0) + holding.get("market_value_yen", 0)
        tickers_by_theme.setdefault(theme, []).append(ticker)

    total_value = sum(totals.values())

    if total_value <= 0:
        return []

    allocation = [
        {
            "theme": theme,
            "value_yen": round(value),
            "ratio_percent": round(value / total_value * 100, 1),
            "tickers": tickers_by_theme[theme],
        }
        for theme, value in totals.items()
    ]

    allocation.sort(key=lambda x: x["ratio_percent"], reverse=True)

    return allocation


def detect_concentration_risks(
    portfolio_impact: dict[str, Any],
    theme_allocation: list[dict[str, Any]],
) -> list[str]:
    """
    集中投資リスクを検知する。

    単一銘柄が資産全体の一定比率(SINGLE_HOLDING_THRESHOLD_PERCENT)を超える場合、
    または特定テーマへの配分が一定比率(SINGLE_THEME_THRESHOLD_PERCENT)を超える場合に、
    その旨を示す短いメッセージを返す。

    Returns:
        リスクを説明する文字列のリスト。該当が無ければ空リスト。
    """
    risks: list[str] = []

    for holding in portfolio_impact.get("holdings", []):
        ratio = holding.get("portfolio_ratio", 0)

        if ratio >= SINGLE_HOLDING_THRESHOLD_PERCENT:
            risks.append(
                f"{holding.get('name', holding.get('ticker'))}"
                f"({holding.get('ticker')})が資産全体の{ratio}%を占めています"
            )

    for theme in theme_allocation:
        if theme["theme"] != OTHER_THEME and theme["ratio_percent"] >= SINGLE_THEME_THRESHOLD_PERCENT:
            risks.append(
                f"「{theme['theme']}」テーマへの配分が資産全体の{theme['ratio_percent']}%に達しています"
            )

    return risks
