from openai import OpenAI
from dotenv import load_dotenv
import os
import sys
import json
from market_data import get_market_data
from news_data import get_market_news
from portfolio_analysis import calculate_portfolio_impact
from earnings_calendar import get_upcoming_earnings
from utils import log_error

from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    PushMessageRequest,
    TextMessage
)

load_dotenv()

# LINEの1メッセージあたりの文字数上限(5000)に余裕を持たせた安全値
LINE_MAX_LENGTH = 4900

# OpenAI設定
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


def send_line_message(text: str) -> bool:
    """
    LINEへメッセージを送信する。

    文字数が上限を超える場合は切り詰めて送信する。

    Returns:
        送信に成功した場合True、失敗した場合False。
        呼び出し側はFalseの場合に異常終了させるかどうかを判断できる。
    """
    if len(text) > LINE_MAX_LENGTH:
        text = text[:LINE_MAX_LENGTH] + "\n\n…(文字数上限のため以降省略)"

    try:
        configuration = Configuration(
            access_token=os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
        )

        with ApiClient(configuration) as api_client:
            line_api = MessagingApi(api_client)

            line_api.push_message(
                PushMessageRequest(
                    to=os.getenv("LINE_USER_ID"),
                    messages=[
                        TextMessage(text=text)
                    ]
                )
            )

        print("LINE送信完了")
        return True

    except Exception as e:
        log_error("LINE送信失敗", e)
        return False


# ポートフォリオ・投資方針の読み込み
# これらは必須データのため、失敗した場合はエラーをLINEに通知して処理を停止する
try:
    with open("portfolio.json", "r", encoding="utf-8") as f:
        portfolio = json.load(f)

    with open("strategy.txt", "r", encoding="utf-8") as f:
        strategy = f.read()

except Exception as e:
    log_error("必須ファイルの読み込みに失敗", e)
    send_line_message(
        "⚠️ EZE起動エラー\n\n"
        "portfolio.jsonまたはstrategy.txtの読み込みに失敗しました。\n\n"
        f"エラー内容: {e}"
    )
    sys.exit(1)


# 市場データ取得
# 失敗してもレポート自体は継続させたいため、空データにフォールバックする
try:
    market_data = get_market_data(portfolio)
except Exception as e:
    log_error("market_data取得失敗", e)
    market_data = {}

print("JPY=X DATA")
print(market_data.get("JPY=X"))


# 決算予定取得(失敗時は空リストで継続)
try:
    earnings = get_upcoming_earnings(portfolio)
except Exception as e:
    log_error("earnings取得失敗", e)
    earnings = []


# ポートフォリオ影響計算(失敗時は空の集計結果で継続)
try:
    portfolio_impact = calculate_portfolio_impact(
        portfolio,
        market_data
    )
except Exception as e:
    log_error("portfolio_impact計算失敗", e)
    portfolio_impact = {
        "summary": {},
        "holdings": []
    }


# ニュースデータ取得(失敗時は空データで継続)
try:
    news_data = get_market_news()
except Exception as e:
    log_error("news_data取得失敗", e)
    news_data = {}


# EZEへの指示
prompt = f"""
{strategy}

以下が現在のポートフォリオです。

{json.dumps(portfolio, ensure_ascii=False, indent=2)}

以下が本日の市場データです。

{json.dumps(market_data, ensure_ascii=False, indent=2)}

以下が本日のニュースです。

{json.dumps(news_data, ensure_ascii=False, indent=2)}

以下が保有銘柄の決算予定です。

{json.dumps(earnings, ensure_ascii=False, indent=2)}

以下がPythonで計算したポートフォリオ影響データです。

{json.dumps(portfolio_impact, ensure_ascii=False, indent=2)}

あなたは私専用の投資秘書「EZE」です。

目的：
忙しい朝に3分以内で、市場状況・保有資産への影響・投資判断を把握できるレポートを作成する。

重要ルール：

・投資判断は5年以上の長期成長投資を前提とする。
・短期的な値動きだけで売買判断しない。
・AI、半導体、量子コンピュータ、次世代エネルギーの長期成長性を重視する。
・ただし「成長テーマだから買い」という判断は禁止。
・企業競争力、市場規模、技術優位性、財務、現在の保有比率、取得価格、リスクを考慮する。
・存在しない情報を推測しない。
・portfolio.jsonに存在しない銘柄は保有銘柄として扱わない。
・sharesが0の銘柄は保有銘柄として表示しない。
・GOOGとGOOGLは別銘柄として保有しているため、両方表示してよい。
・IONLは現在shares=0のため、保有銘柄分析には表示しない。


━━━━━━━━━━
📈 EZE Morning Report
━━━━━━━━━━


【1. 今日の市場】

以下を簡潔に表示。

・S&P500
・NASDAQ
・Dow Jones
・VIX
・米10年債
・ドル円

形式：

銘柄：
数値：
前日比：

その後、市場テーマを3行以内で説明。


【2. 保有銘柄への影響】

重要な銘柄のみ表示。

対象条件：

・前日比±5%以上
・または資産影響額5万円以上
・または決算予定が近い重要銘柄
・または市場テーマ上重要な銘柄

全銘柄を羅列しない。

形式：

銘柄：
株価変化：
コメント：

portfolio.jsonに存在する保有銘柄のみ対象。

投資信託：
・S&P500
・AI_INDEX

その他枠：
・Quantum_Other
・OTHER_US

は表示しない。


【3. 今日の投資判断】

必ず以下の形式。

🟢 買い増し検討

銘柄：
理由：

🟡 保有継続

銘柄：
理由：

🔴 注意・警戒

銘柄：
理由：

短期下落だけで警戒判定しない。

長期成長性とリスクのバランスで判断。


【4. 今日チェックするニュース】

重要度が高いもの最大5件。

選定基準：

・保有銘柄への影響
・市場全体への影響
・今後1週間以内の投資判断への影響

各ニュース：

日本時間○月○日○:○の記事

何が起きたか：
市場への影響：
保有銘柄への影響：

英語タイトルは禁止。

ニュースが投資判断に不要な場合は省略。


【5. EZEアクション】

以下の形式を必ず使用。


📌 今週の方針


🟢 今買い増し候補

最大3銘柄。

銘柄：
理由：


🟡 押し目待ち

最大5銘柄。

銘柄：
理由：


🔴 追加購入停止

最大3銘柄。

銘柄：
理由：


判断基準：

・長期成長性
・企業競争力
・現在評価
・保有比率
・リスク
・追加購入による集中度

を考慮する。


特に量子関連について：

量子関連を一括で否定しない。

以下を区別する。

・技術力、資金力、市場ポジションが比較的強い企業
・投機性が高くリスクが大きい企業

単純に「量子だから危険」という判断は禁止。


【6. EZEから一言】

私の投資方針：

AI
半導体
量子コンピュータ
次世代エネルギー

を踏まえて短いコメント。


【7. ポートフォリオリスク分析】

通常日は簡潔。

以下の場合のみ表示。

・個別銘柄が1日5%以上変動
・資産影響5万円以上
・特定テーマへの集中リスク

最大3行。


【8. 今日の資産影響】

必ずportfolio_impactの数値のみを使用してください。

表示内容

・現在の評価額合計
・取得額合計
・含み損益（円・％）
・前日比（金額）
・プラス寄与TOP3
・マイナス寄与TOP3

現在の評価額や含み損益は推測せず、
portfolio_impactに含まれる

market_value_yen
cost_yen
unrealized_yen
today_impact_yen

を合計して算出してください。

存在しない銘柄や推測は禁止します。


【9. 決算予定】

決算予定がある銘柄のみ表示。

ない場合は項目自体を省略。

表示：

銘柄：
決算発表日：
決算まであと何日：
重要度：
市場予想：
投資判断への影響：
決算で確認すべきポイント：


注意：

・長文禁止
・スマホで読みやすくする
・一般論は禁止
・必ず提供されたポートフォリオに基づく
・数値がある場合は数値を使用
"""

# AI分析生成
# ここが失敗すると本来レポートが1通も届かなくなるため、
# 失敗時はエラー内容そのものをLINEに送ることで「今日は失敗した」と分かるようにする
try:
    response = client.responses.create(
        model="gpt-5-nano",
        input=prompt
    )
    message = response.output_text

except Exception as e:
    log_error("AI分析生成失敗", e)
    message = (
        "⚠️ EZEレポート生成エラー\n\n"
        "本日のレポート作成中にAI分析でエラーが発生しました。\n"
        f"エラー内容: {e}\n\n"
        "データ取得自体は成功している可能性があります。"
        "GitHub Actionsのログを確認してください。"
    )

print(message)


# LINE送信
# 送信に失敗した場合はGitHub Actions側で失敗として検知できるよう
# 終了コード1で終了する(Actionsの実行履歴が赤くなり気づける)
if not send_line_message(message):
    sys.exit(1)
