import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta


def get_news(keyword, limit=3):

    query = urllib.parse.quote(keyword)

    url = (
        "https://news.google.com/rss/search?"
        f"q={query}&hl=en-US&gl=US&ceid=US:en"
    )

    try:
        response = urllib.request.urlopen(url)
        xml = response.read()

        root = ET.fromstring(xml)

        news = []

        for item in root.findall(".//item")[:limit]:

    title = item.find("title").text

    pub_date = item.find("pubDate").text

    try:
        # RSS日時を解析
        dt = datetime.strptime(
            pub_date,
            "%a, %d %b %Y %H:%M:%S %Z"
        )

        # UTC → 日本時間
        japan_time = dt.replace(
            tzinfo=timezone.utc
        ).astimezone(
            timezone(timedelta(hours=9))
        )

        formatted_date = japan_time.strftime(
            "%Y年%m月%d日 %H:%M"
        )

    except:
        formatted_date = "日時取得不可"


    news.append(
        {
            "title": title,
            "date_japan": formatted_date
        }
    )

        return news

    except Exception as e:
        return [f"ニュース取得エラー: {e}"]



def get_market_news():

    targets = {
        "AI・半導体": "NVIDIA OR AI semiconductor",
        "量子コンピュータ": "IonQ OR Rigetti quantum computing",
        "米国市場": "US stock market Federal Reserve",
        "金利": "US Treasury yield Federal Reserve"
    }

    result = {}

    for category, keyword in targets.items():
        result[category] = get_news(keyword)

    return result
