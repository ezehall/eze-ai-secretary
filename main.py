from openai import OpenAI
from dotenv import load_dotenv
import os
import json
from market_data import get_market_data
from news_data import get_market_news
from portfolio_analysis import calculate_portfolio_impact
from earnings_calendar import get_upcoming_earnings

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

earnings = get_upcoming_earnings(portfolio)

portfolio_impact = calculate_portfolio_impact(
    portfolio,
    market_data
)

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
。

以下が保有銘柄の決算予定です。

{json.dumps(earnings, ensure_ascii=False, indent=2)}

以下が本日のポートフォリオ損益影響です。

{json.dumps(portfolio_impact, ensure_ascii=False, indent=2)}

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
現在のportfolio.jsonに登録されている保有銘柄を対象にしてください。

ただし、
S&P500投資信託
OTHER_US
Quantum_Other
など個別株ではないものは除外してください。


【3. 今日の投資判断】

以下を必ず分類。

🟢 買い増し検討
🟡 保有継続
🔴 注意・警戒

理由を1〜2行で説明。


【4. 今日チェックするニュース】

ニュースタイトルの前に必ず、
「日本時間○月○日○時の記事」
と表示してください。
取得したニュースを日本語で要約してください。

重要度の高いニュースを最大5件まで選択してください。

選択基準：
・保有銘柄への影響度
・株価変動への影響度
・今後1週間以内の投資判断への重要性

重要度の低いニュースは省略してください。

各ニュースについて、

・何が起きたか
・市場への影響
・私の保有銘柄への影響

を3〜4行で説明してください。

英語タイトルの転載は禁止。

【5. EZEアクション】

現在のポートフォリオと市場環境を踏まえて、
今後の投資行動について具体的に提案してください。

以下の形式：

📌 今週の方針

買い増し候補：
・銘柄名
・理由

追加購入を控える銘柄：
・銘柄名
・理由

注意すべきリスク：
・金利
・決算
・過熱感
・ポートフォリオ集中度
など

判断基準：
短期的な値動きではなく、
5年以上の長期成長投資方針を前提にしてください。

特に、
・AI
・半導体
・量子コンピュータ
・次世代エネルギー

の長期成長性とリスクを評価してください。

【6. EZEから一言】

あなたの投資方針
（AI・半導体・量子など成長テーマ重視）
を踏まえた短いコメント。

【7. 今日の資産影響】

保有金額を考慮して、
どの銘柄が資産全体へ影響したか分析してください。

単純な株価変動率ではなく、
金額影響を重視してください。

【8. 決算予定】

以下の決算予定銘柄について分析してください。

必ず以下の形式で表示してください。

銘柄：
決算発表日：
決算まであと何日：
重要度：（★★★★★〜★）

市場予想：
・EPS：
・売上：

投資判断への影響：
（保有継続、買い増し判断、警戒ポイントなど）

決算で確認すべきポイント：
・売上成長率
・利益率
・会社見通し
・AI関連投資効果
など、その銘柄に合わせて記載してください。

特に保有金額が大きい銘柄、成長テーマの中心銘柄を優先してください。

決算予定がない場合は、
「30日以内に重要決算予定なし」
とだけ表示してください。

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
