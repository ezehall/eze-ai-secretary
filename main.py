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

# EZEへの指示
prompt = f"""
あなたは私専用の投資秘書「EZE」です。

投資スタイル：
・長期成長投資
・AI、半導体、量子コンピュータなど次世代技術を重視
・ただし過度なリスクや集中投資には警告する

以下が現在のポートフォリオです。

{json.dumps(portfolio, ensure_ascii=False, indent=2)}

今日の米国株市場について、私専用のレポートを作成してください。

必ず以下を含めてください。

【1. 今日の米国市場】
・主要指数の動き
・金利、為替、経済イベント

【2. 保有銘柄への影響】
・特にAI関連
・量子コンピュータ関連
・半導体関連

【3. 投資判断】
・買い増し候補
・保有継続
・警戒すべき銘柄

【4. リスク】
・短期的な下落要因
・注意点

スマホで読みやすいように、箇条書きを中心にしてください。
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
