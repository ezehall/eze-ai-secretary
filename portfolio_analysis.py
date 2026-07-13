def calculate_portfolio_impact(portfolio, market_data):

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

            cost = shares * average_price
            market_value = shares * current_price
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

        impact = amount * (change / 100)

        results.append({
            "ticker": ticker,
            "name": item["name"],
            "amount_yen": round(amount),
            "change_percent": change,
            "impact_yen": round(impact)
        })

    results.sort(
        key=lambda x: x["impact_yen"],
        reverse=True
    )

    return results
def format_portfolio_impact(results):

    text = "【6. 今日の資産影響】\n\n"

    total = 0

    for item in results:

        total += item["impact_yen"]

        sign = "+" if item["impact_yen"] >= 0 else ""

        text += (
            f"{item['name']}\n"
            f"保有額：約{item['amount_yen']:,}円\n"
            f"前日比：{item['change_percent']}%\n"
            f"影響：{sign}{item['impact_yen']:,}円\n\n"
        )

    text += (
        f"本日の推定変動額："
        f"{'+' if total >= 0 else ''}{total:,}円"
    )

    return text
