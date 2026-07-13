import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
import pytz
from datetime import datetime, timezone, timedelta

def convert_japan_time(date_string):

    try:
        dt = parsedate_to_datetime(date_string)

        japan = pytz.timezone("Asia/Tokyo")

        dt_japan = dt.astimezone(japan)

        return dt_japan.strftime(
            "%Y年%m月%d日 %H:%M"
        )

    except:
        return "日時不明"

def get_news(keyword, limit=2):

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

            news.append(
    {
        "title": title,
        "date": convert_japan_time(pub_date)
    }
            )

        return news

    except Exception as e:
        return [
            {
                "error": f"ニュース取得エラー: {e}"
            }
        ]



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
