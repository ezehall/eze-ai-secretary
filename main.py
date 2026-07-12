from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

response = client.responses.create(
    model="gpt-5-nano",
    input="あなたは優秀な投資アシスタントです。今日の米国株市場を見るうえで重要なポイントを3つ教えてください。"
)

print("=== EZE START ===")
print(response.output_text)
print("=== EZE END ===")
