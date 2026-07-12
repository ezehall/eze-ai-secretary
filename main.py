from openai import OpenAI
from dotenv import load_dotenv
import os
import json
from market_data import get_market_data
from news_data import get_market_news

from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    PushMessageRequest,
    TextMessage
)

load_dotenv()

# OpenAI設定
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

# ポートフォリオ読み込み
with open("portfolio.json", "r", encoding="utf-8") as f:
    portfolio = json.load(f)
# 市場データ取得
market_data = get_market_data()    
# ニュースデータ取得
news_data = get_market_news()
# 投資方針読み込み
with open("strategy.txt", "r", encoding="utf-8") as f:
    strategy = f.read()    

# EZEへの指示
prompt = f"""
{strategy}

以下が現在のポートフォリオです。

{json.dumps(portfolio, ensure_ascii=False, indent=2)}

以下が本日の市場データです。

{json.dumps(market_data, ensure_ascii=False, indent=2)}

以下が本日のニュースです。

{json.dumps(news_data, ensure_ascii=False, indent=2)}

あなたは私専用の投資秘書「EZE」です。

以下の情報をもとに、毎朝読むための短い投資レポートを作成してください。

目的：
忙しい朝に3分以内で市場状況と投資判断が理解できる内容にする。

必ず以下の形式で作成してください。

━━━━━━━━━━
📈 EZE Morning Report
━━━━━━━━━━

【1. 今日の市場】

・S&P500
・NASDAQ
・Dow Jones
・VIX
・米10年債
・ドル円

について、
数値と前日比を簡潔に表示。

その後、
今日の市場テーマを3行以内で説明。


【2. 保有銘柄への影響】

重要な銘柄だけ記載。

以下の形式：

銘柄：
株価変化：
コメント：

対象：
・NVDA
・GOOGL
・AVGO
・ARM
・MU
・IONQ
・IONL
・RGTI
・ARQQ
・OKLO


【3. 今日の投資判断】

以下を必ず分類。

🟢 買い増し検討
🟡 保有継続
🔴 注意・警戒

理由を1〜2行で説明。


【4. 今日チェックするニュース】

今後影響しそうな材料を3つ。


【5. EZEから一言】

あなたの投資方針
（AI・半導体・量子など成長テーマ重視）
を踏まえた短いコメント。


注意：
・長文は禁止
・一般論ではなく、提供されたポートフォリオに基づいて判断する
・数値がある場合は必ず数値を使う
・スマホで読みやすくする
"""

# AI分析生成
response = client.responses.create(
    model="gpt-5-nano",
    input=prompt
)

message = response.output_text

print(message)


# LINE送信
configuration = Configuration(
    access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
)

with ApiClient(configuration) as api_client:
    line_api = MessagingApi(api_client)

    line_api.push_message(
        PushMessageRequest(
            to=os.getenv("LINE_USER_ID"),
            messages=[
                TextMessage(text=message)
            ]
        )
    )

print("LINE送信完了")
