def calculate_portfolio_impact(portfolio, market_data):
    usd_jpy = market_data["JPY=X"]["price"]
    results = []

    for item in portfolio["holdings"]:

        ticker = item["ticker"]

        if ticker not in market_data:
            continue

        data = market_data[ticker]

        if "price" not in data:
            continue

        current_price = data["price"]
        change = data["change_percent"]

        # 日本株・米国株
        if "shares" in item:

            shares = item["shares"]
            average_price = item["average_price"]

            # 日本株は円、米国株はドル→円換算
if ticker.isdigit():
    cost = shares * average_price
    market_value = shares * current_price
else:
    cost = shares * average_price * usd_jpy
    market_value = shares * current_price * usd_jpy

today_impact = market_value * (change / 100)

        # 投資信託
        elif "units" in item:

            units = item["units"]
            average_price = item["average_price"]

            cost = average_price * units / 10000
            market_value = current_price * units / 10000
            today_impact = market_value * (change / 100)

        else:
            continue

        unrealized = market_value - cost

        results.append({
            "ticker": ticker,
            "name": item["name"],
            "cost_yen": round(cost),
            "market_value_yen": round(market_value),
            "unrealized_yen": round(unrealized),
            "unrealized_percent": round(unrealized / cost * 100, 2) if cost else 0,
            "today_change_percent": change,
            "today_impact_yen": round(today_impact)
        })

    results.sort(
        key=lambda x: x["today_impact_yen"],
        reverse=True
    )

    return results
