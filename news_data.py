"""
ニュース取得モジュール。

Google News RSSから、投資テーマに関連するニュースをカテゴリ別に取得する。
"""

import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from typing import Any

import pytz

REQUEST_TIMEOUT_SECONDS = 10
USER_AGENT = "Mozilla/5.0 (compatible; EZE-Investment-Secretary/1.0)"

# カテゴリ名: 検索キーワード
NEWS_TARGETS: dict[str, str] = {
    "AI・半導体": "NVIDIA OR AI semiconductor",
    "量子コンピュータ": "IonQ OR Rigetti quantum computing",
    "米国市場": "US stock market Federal Reserve",
    "金利": "US Treasury yield Federal Reserve",
}


def convert_japan_time(date_string: str) -> str:
    """
    RFC822形式の日時文字列(RSSのpubDate)を日本時間の表示用文字列に変換する。

    変換に失敗した場合は "日時不明" を返す。
    """
    try:
        dt = parsedate_to_datetime(date_string)
        japan = pytz.timezone("Asia/Tokyo")
        dt_japan = dt.astimezone(japan)
        return dt_japan.strftime("%Y年%m月%d日 %H:%M")

    except (TypeError, ValueError) as e:
        print(f"日時変換失敗: {date_string} / {e}")
        return "日時不明"


def get_news(keyword: str, limit: int = 2) -> list[dict[str, Any]]:
    """
    指定キーワードでGoogle News RSSを検索し、最新ニュースを取得する。

    Args:
        keyword: 検索キーワード
        limit: 取得件数の上限

    Returns:
        {"title": str, "date": str, "url": str} の辞書のリスト。
        取得に失敗した場合は {"error": str} を1件含むリストを返す。
    """
    query = urllib.parse.quote(keyword)
    url = (
        "https://news.google.com/rss/search?"
        f"q={query}&hl=en-US&gl=US&ceid=US:en"
    )

    try:
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            xml_data = response.read()

        root = ET.fromstring(xml_data)

        news: list[dict[str, Any]] = []

        for item in root.findall(".//item")[:limit]:
            title = item.find("title")
            pub_date = item.find("pubDate")
            link = item.find("link")

            news.append({
                "title": title.text if title is not None else "タイトル不明",
                "date": convert_japan_time(pub_date.text) if pub_date is not None else "日時不明",
                "url": link.text if link is not None else None,
            })

        return news

    except Exception as e:
        print(f"ニュース取得失敗: {keyword} / {e}")
        return [{"error": f"ニュース取得エラー: {e}"}]


def get_market_news() -> dict[str, list[dict[str, Any]]]:
    """カテゴリ別に市場ニュースを取得する。"""
    return {
        category: get_news(keyword)
        for category, keyword in NEWS_TARGETS.items()
    }
