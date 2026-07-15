from openai import OpenAI
from dotenv import load_dotenv
import os
import sys
import json
from market_data import get_market_data
from news_data import get_market_news
from portfolio_analysis import calculate_portfolio_impact
from portfolio_insights import calculate_theme_allocation, detect_concentration_risks
from valuation_data import get_valuation_data
from earnings_calendar import get_upcoming_earnings, get_recent_earnings_results
from trade_processor import load_trade_history, apply_trades
from asset_history import append_daily_snapshot
from risk_analytics import calculate_volatility, calculate_correlation
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


# 売買履歴の反映(Phase3)
# trade_history.json内の未反映(applied=false)の売買をportfolio.jsonへ反映する。
# ファイルが存在しない場合は何もしない(未導入でも動作する)。
# ここで反映しておくことで、本日のレポートにも更新後の保有状況が使われる。
trade_errors: list[str] = []
try:
    trades = load_trade_history()
    portfolio, trades, trade_errors, trades_changed = apply_trades(portfolio, trades)

    if trades_changed:
        with open("portfolio.json", "w", encoding="utf-8") as f:
            json.dump(portfolio, f, ensure_ascii=False, indent=2)

        with open("trade_history.json", "w", encoding="utf-8") as f:
            json.dump(trades, f, ensure_ascii=False, indent=2)

        print(f"売買履歴を反映しました({sum(1 for t in trades if t.get('applied'))}件適用済み)")

except Exception as e:
    log_error("売買履歴の反映処理に失敗", e)


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


# 直近決算の実績振り返り取得(失敗時は空リストで継続)
try:
    recent_earnings_results = get_recent_earnings_results(portfolio)
except Exception as e:
    log_error("recent_earnings_results取得失敗", e)
    recent_earnings_results = []


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


# テーマ別配分・集中投資リスクの計算(Phase2)
# 比率や集中度はAIに推測させず、Python側で確定計算した数値をそのまま使わせる
try:
    theme_allocation = calculate_theme_allocation(portfolio, portfolio_impact)
    concentration_risks = detect_concentration_risks(portfolio_impact, theme_allocation)
except Exception as e:
    log_error("ポートフォリオ分析(テーマ配分・集中リスク)計算失敗", e)
    theme_allocation = []
    concentration_risks = []


# バリュエーションデータ(PER・PBR・PEG等)の取得(Phase2)
# 失敗時は空リストで継続する(割高・割安判断が定性コメントのみになる)
try:
    valuation_data = get_valuation_data(portfolio)
except Exception as e:
    log_error("valuation_data取得失敗", e)
    valuation_data = []


# 資産推移ログの記録(基盤系)
# 失敗してもレポート自体には影響させない(ログ記録の失敗でレポートが
# 届かなくなるのは本末転倒なため)
try:
    asset_history = append_daily_snapshot(portfolio_impact)
except Exception as e:
    log_error("資産推移ログの記録に失敗", e)
    asset_history = []


# ボラティリティ・相関分析(Phase2積み残し)
# asset_history.jsonの蓄積日数が少ないうちはavailable=Falseとなり、
# AIには「データ蓄積中」であることをそのまま伝える
try:
    volatility_data = calculate_volatility(asset_history)
    correlation_data = calculate_correlation(asset_history)
except Exception as e:
    log_error("リスク分析(ボラティリティ・相関)計算失敗", e)
    volatility_data = {"available": False, "data_points": 0, "volatility": []}
    correlation_data = {"available": False, "data_points": 0, "top_pairs": []}


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
days_untilとpre_earnings_alertはPython側で確定計算済みなので、
自分で日数を計算し直さず、この値をそのまま使ってください。

{json.dumps(earnings, ensure_ascii=False, indent=2)}

以下が直近{3}日以内に発表された保有銘柄の決算実績(市場予想との比較)です。
まだ実績が発表されていない銘柄はここには含まれません。空リストの場合は
直近の決算発表が無かったことを意味します。

{json.dumps(recent_earnings_results, ensure_ascii=False, indent=2)}

以下がPythonで計算したポートフォリオ影響データです。

{json.dumps(portfolio_impact, ensure_ascii=False, indent=2)}

以下がPythonで計算したテーマ別配分データです(比率はvalue_yenの合計に対する割合、%)。
この数値をそのまま使い、自分で比率を計算し直さないでください。

{json.dumps(theme_allocation, ensure_ascii=False, indent=2)}

以下がPythonで検知した集中投資リスクです。空リストの場合は集中リスクなしを意味します。

{json.dumps(concentration_risks, ensure_ascii=False, indent=2)}

以下がFMP APIから取得した評価指標(PER・PBR・PEG・PSR、いずれも直近12ヶ月ベース)です。
値がnullの項目はデータが取得できなかったことを意味するので、その項目については
「データなし」として扱い、憶測で数値を補わないでください。この数値はそのまま使い、
自分でPER等を計算し直さないでください。

{json.dumps(valuation_data, ensure_ascii=False, indent=2)}

以下がPythonで計算したボラティリティ(値動きの標準偏差)データです。
availableがfalseの場合はデータ蓄積中のため、無理に分析コメントを書かず、
「データ蓄積中(現在data_points日分/required_data_points日分必要)」と
一言添えるだけにしてください。

{json.dumps(volatility_data, ensure_ascii=False, indent=2)}

以下がPythonで計算した銘柄間の相関データ(相関が高いペア上位)です。
availableがfalseの場合の扱いはボラティリティと同様です。

{json.dumps(correlation_data, ensure_ascii=False, indent=2)}

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
・比率や金額などの数値はPythonが計算した値のみを使い、自分で計算し直さない。
・portfolio.jsonに存在しない銘柄は保有銘柄として扱わない。
・sharesが0の銘柄は保有銘柄として表示しない。
・GOOGとGOOGLは別銘柄として保有しているため、両方表示してよい。ただし同一発行体(Alphabet)の
  異なる株式クラスであるため、【3. 投資アクション】でGOOGとGOOGLの方向性(買い増し/ホールド/利確/
  停止)が互いに矛盾しないようにすること。保有比率や取得単価の違いにより結論が異なる場合は、
  その理由を理由欄に明記すること。
・IONLは現在shares=0のため、保有銘柄分析には表示しない。
・各セクションの指示文(「〇行以内」「重要な銘柄のみ表示」等の条件説明や見出しの注釈)は、
  出力に一切含めない。指示に従った結果のみを書くこと。
・Pythonから渡されたデータ(集中投資リスクなど)をリストのまま(例: ["...", "..."])貼り付けない。
  自然な日本語の箇条書き(・から始まる行)に整形してから表示すること。


━━━━━━━━━━
📈 EZE Morning Report
━━━━━━━━━━


【1. 市場概況】

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


【3. 投資アクション】

必ず以下の4分類のみを使う。日次と週次で内容を分けて重複させない(1つの結論として書く)。

🟢 買い増し検討(最大3銘柄)
銘柄：
理由：

🟡 ホールド推奨(該当する代表的な銘柄のみ)
銘柄：
理由：

🔴 利確検討(含み益が大きく、リスクに見合わないと判断される場合のみ)
銘柄：
理由：

⛔ 追加購入停止(集中投資リスクや過熱感が高い銘柄)
銘柄：
理由：

該当銘柄が無い分類はその項目ごと省略してよい。

判断基準：
・長期成長性
・企業競争力
・現在評価
・保有比率
・リスク
・追加購入による集中度

特に量子関連について：
量子関連を一括で否定しない。技術力・資金力・市場ポジションが比較的強い企業と、
投機性が高くリスクが大きい企業を区別する。単純に「量子だから危険」という判断は禁止。


【4. ポートフォリオ分析】

必ず以下の順で表示する。

■ テーマ別配分
上記のテーマ別配分データを比率が高い順にそのまま表示。
形式：テーマ名：比率%(評価額)

■ 集中投資リスク
上記の集中投資リスクデータの各項目を「・」で始まる箇条書きに変換して表示すること
(リストの角括弧やダブルクォートをそのまま出力しない)。
データが空リストの場合は「・特になし」と1行だけ表示。

■ 割高・割安分析
上記の評価指標データ(valuation_data)をもとに、主要な保有銘柄についてPER・PEGレシオを
中心に割高感・割安感を短く述べる。数値が「データなし」の銘柄は無理に評価しない。
形式：
銘柄：PER〇倍(データなしの場合は省略)／所見(1行)
最大5銘柄程度に絞り、羅列しすぎない。

■ ボラティリティ・相関
volatility_data・correlation_dataがavailable=trueの場合のみ、ボラティリティが高い上位2〜3銘柄と、
相関が高い(または低い)銘柄ペアを1〜2行で述べる。availableがfalseの場合は
「データ蓄積中(あとX日分)」とだけ書き、それ以上の考察はしない。

■ EZEの所見(4行以内)
保有銘柄全体を俯瞰した所見をまとめる。含める観点：
・ポートフォリオ全体として割高/割安に偏っている傾向があるか(上記の評価指標を踏まえる)
・長期成長性の観点でポートフォリオ全体はどう評価できるか
・リバランスやポートフォリオ改善の方向性があれば一言
個別銘柄の説明を繰り返さず、あくまでポートフォリオ全体の視点で書くこと。


【5. 今日チェックするニュース】

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
リンク：(そのニュースのurlの値をそのまま記載。urlがnullの場合はこの行自体を省略)

英語タイトルは禁止。

ニュースが投資判断に不要な場合は省略。


【6. 今日の資産影響】

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


【7. 決算予定】

■ 決算予定
決算予定がある銘柄のみ表示。

ない場合は項目自体を省略。

表示形式は以下を厳守する。「銘柄：」の行は常にこの形式で書き、
pre_earnings_alertがtrueの場合のみ銘柄名の直後に半角スペースと⚠️を付ける
(falseの場合は⚠️を付けず、括弧などの余分な記号も付けない)。

例(アラートあり)：銘柄：TSM ⚠️
例(アラートなし)：銘柄：PLTR

表示：

銘柄：
決算発表日：
決算まであと何日：(days_untilの値をそのまま使う)
重要度：
市場予想：
投資判断への影響：
決算で確認すべきポイント：

■ 直近決算の振り返り
recent_earnings_resultsが空リストの場合はこのサブセクション自体を省略する。
データがある場合、各銘柄について以下を表示する。

銘柄：
予想EPS/実績EPS：
サプライズ：(eps_surprise_percentを%表示。ポジティブなら上振れ、ネガティブなら下振れと分かる書き方)
決算後の想定リスク：(サプライズの大小を踏まえ、株価への影響や注視点を2行以内で)


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

# 売買履歴の反映でエラーがあった場合、AIの出力に頼らずPython側で
# 確実にメッセージ先頭へ警告を追加する(該当分はtrade_history.json上で
# 未反映のままなので、内容を修正すれば次回以降に再度反映を試みる)
if trade_errors:
    warning_lines = "\n".join(f"・{e}" for e in trade_errors)
    message = (
        "⚠️ 売買履歴の反映で問題がありました(該当分は未反映です。"
        "trade_history.jsonの内容を修正してください)\n"
        f"{warning_lines}\n\n"
        "━━━━━━━━━━\n\n"
    ) + message


# LINE送信
# 送信に失敗した場合はGitHub Actions側で失敗として検知できるよう
# 終了コード1で終了する(Actionsの実行履歴が赤くなり気づける)
if not send_line_message(message):
    sys.exit(1)
