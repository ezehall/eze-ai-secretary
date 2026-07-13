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


        # 投信・その他枠を除外
        if ticker in exclude_tickers:
            continue


        # 株数がないものは除外
        if "shares" not in item:
            continue


        # 0株は除外
        if item["shares"] <= 0:
            continue


        # 市場データなし
        if ticker not in market_data:
            continue


        data = market_data[ticker]


        # 株価なし
        if "price" not in data:
            continue


        if "change_percent" not in data:
            continue


        current_price = data["price"]
        change = data["change_percent"]


        shares = item["shares"]
        average_price = item["average_price"]


        # 日本株
        if item.get("currency") == "JPY":

            cost = shares * average_price

            market_value = shares * current_price


        # 米国株・ETF
        else:

            cost = shares * average_price * usd_jpy

            market_value = shares * current_price * usd_jpy



        today_impact = market_value * (change / 100)


        unrealized = market_value - cost


        total_cost += cost
        total_market_value += market_value
        total_today_impact += today_impact



        results.append({

            "ticker": ticker,

            "name": item["name"],

            "cost_yen": round(cost),

            "market_value_yen": round(market_value),

            "unrealized_yen": round(unrealized),

            "unrealized_percent":
                round(
                    unrealized / cost * 100,
                    2
                )
                if cost else 0,

            "today_change_percent": change,

            "today_impact_yen": round(today_impact)

        })


    # 前日比影響額が大きい順
    results.sort(
        key=lambda x: x["today_impact_yen"],
        reverse=True
    )


    summary = {

        "total_cost_yen":
            round(total_cost),

        "total_market_value_yen":
            round(total_market_value),

        "total_unrealized_yen":
            round(
                total_market_value - total_cost
            ),

        "total_unrealized_percent":
            round(
                (total_market_value - total_cost)
                / total_cost * 100,
                2
            )
            if total_cost else 0,

        "total_today_impact_yen":
            round(total_today_impact)

    }


    return {

        "summary": summary,

        "holdings": results

    }
