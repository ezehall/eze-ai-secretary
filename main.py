from openai import OpenAI
from dotenv import load_dotenv
import os
import json

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

prompt = f"""
あなたは私専用の投資アシスタントです。

以下は私の保有銘柄です。

{json.dumps(portfolio, ensure_ascii=False, indent=2)}

今日の米国株市場について、
私のポートフォリオへの影響を中心に分析してください。

以下を含めてください。

・今日注目すべきニュース
・保有銘柄への影響
・AI関連株の動向
・量子コンピュータ関連株の動向
・リスク要因
・今日の投資判断ポイント

読みやすく、スマホで見やすい文章にしてください。
"""

response = client.responses.create(
    model="gpt-5-nano",
    input=prompt
)

message = response.output_text

print(message)

print("TOKEN exists:", bool(os.getenv("LINE_CHANNEL_ACCESS_TOKEN")))
print("USER exists:", bool(os.getenv("LINE_USER_ID")))
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
