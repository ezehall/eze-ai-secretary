from flask import Flask, request
import os

app = Flask(__name__)

@app.route("/callback", methods=["POST"])
def callback():
    body = request.json

    print(body)

    return "OK"

if __name__ == "__main__":
    app.run()
