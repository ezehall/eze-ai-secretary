def calculate_portfolio_impact(portfolio, market_data):

    # USD/JPY取得
    if "JPY=X" in market_data and "price" in market_data["JPY=X"]:
        usd_jpy = market_data["JPY=X"]["price"]
    else:
        usd_jpy = 150

    results = []

    total_cost = 0
    total_market_value = 0
    total_today_impact = 0

    # 除外対象
    exclude_tickers = [
        "S&P500",
        "AI_INDEX",
        "Quantum_Other",
        "OTHER_US"
    ]

    for item in portfolio["holdings"]:

        ticker = item["ticker"]

        # 投資信託・その他枠を除外
        if ticker in exclude_tickers:
            continue

        # 株式・ETF以外を除外
        if "shares" not in item:
            continue

        # 0株保有は除外
        if item["shares"] <= 0:
            continue

        # 市場データがない場合
        if ticker not in market_data:
            continue

        data = market_data[ticker]

        # 株価データがない場合
        if "price" not in data:
            continue

        if "change_percent" not in data:
