from openai import OpenAI
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

with open("portfolio.json", "r", encoding="utf-8") as f:
    portfolio = json.load(f)

prompt = f"""
あなたは優秀な投資アシスタントです。

以下は私の保有銘柄です。

{json.dumps(portfolio, ensure_ascii=False, indent=2)}

このポートフォリオを踏まえて、
今日の米国株市場で注目すべきポイントを3つ教えてください。

特に以下を重視してください。
・保有銘柄への影響
・AI関連株
・量子コンピュータ関連株
・リスク要因

初心者にも分かるように説明してください。
"""

response = client.responses.create(
    model="gpt-5-nano",
    input=prompt
)

print("=== EZE AI Secretary ===")
print(response.output_text)
