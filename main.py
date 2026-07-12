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
# 投資方針読み込み
with open("strategy.txt", "r", encoding="utf-8") as f:
    strategy = f.read()    

# EZEへの指示
prompt = f"""
{strategy}

以下が現在のポートフォリオです。

{json.dumps(portfolio, ensure_ascii=False, indent=2)}

今日の米国株市場について、
私専用の投資レポートを作成してください。

以下を含めてください。

【市場分析】
・米国主要指数
・金利
・為替
・市場全体の流れ

【保有銘柄への影響】
・AI関連
・半導体関連
・量子コンピュータ関連
・その他保有銘柄

【投資判断】
・買い増し検討
・保有継続
・警戒ポイント

【リスク】
・短期的リスク
・長期的リスク

スマホで読みやすいように箇条書き中心で作成してください。
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
