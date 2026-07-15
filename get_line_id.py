"""
LINE公式アカウントのWebhookを受信し、送られてきたUser IDを確認するための
ローカル動作確認用スクリプト。

main.pyの日次実行パイプラインとは無関係。
LINE_USER_IDを取得したい時にのみ手動で起動する。
"""

from typing import Any

from flask import Flask, request

app = Flask(__name__)


@app.route("/callback", methods=["POST"])
def callback() -> str:
    """LINEからのWebhookイベントをそのまま標準出力に表示する。"""
    body: Any = request.json
    print(body)
    return "OK"


if __name__ == "__main__":
    app.run()
