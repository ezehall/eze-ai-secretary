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
IONLだけは特別含んでください。


【3. 今日の投資判断】

以下を必ず分類。

🟢 買い増し検討
🟡 保有継続
🔴 注意・警戒

理由を1〜2行で説明。


【4. 今日チェックするニュース】

ニュースタイトルの前に必ず、
「日本時間○月○日○:○の記事」
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

買い判断は以下の3段階で評価してください。

🟢 今買い増し候補
🟡 押し目待ち
🔴 追加購入停止

単純に成長テーマだから買い推奨は禁止。
現在の評価、リスク、保有比率も考慮してください。

【6. EZEから一言】

あなたの投資方針
（AI・半導体・量子など成長テーマ重視）
を踏まえた短いコメント。

【7. ポートフォリオリスク分析】

毎日は詳細分析を表示しない。

以下の場合のみ簡潔に表示する。

・特定銘柄が1日5%以上変動した場合
・資産全体への影響が5万円以上の場合
・保有比率が大きく変化した場合

表示する場合は、
最大3行以内でまとめる。

【8. 今日の資産影響】

必ずportfolio_impactの数値のみを使用してください。

表示内容：

・現在の評価額合計
・含み損益合計（円・％）
・前日比（金額）
・プラス寄与TOP3
・マイナス寄与TOP3

portfolio_impactに含まれる

market_value_yen
unrealized_yen
unrealized_percent
today_impact_yen

のみを使って計算してください。

推測は禁止。
存在しない数値は禁止。

【9. 決算予定】

取得した決算予定データを分析してください。

決算予定がある場合：
・予定銘柄のみ表示する。
・「30日以内に重要決算予定なし」は絶対に表示しない。
・決算予定がある銘柄について、以下を表示する。

銘柄：
決算発表日：
決算まであと何日：
重要度：
市場予想：
投資判断への影響：
決算で確認すべきポイント：

注意：
決算予定が存在しない場合、この項目自体を省略してください。
「決算予定なし」
「30日以内に重要決算予定なし」
などの文章は一切表示しないでください。

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
