def calculate_portfolio_impact(portfolio, market_data):

    results = []

    for item in portfolio["holdings"]:

        ticker = item["ticker"]

        if ticker not in market_data:
            continue

        change = market_data[ticker].get("change_percent")

        if change is None:
            continue

        # 旧形式(amount_yen)
        if "amount_yen" in item:
            amount = item["amount_yen"]

        # 新形式(株数 × 平均取得単価)
        elif "shares" in item and "average_price" in item:

            amount = item["shares"] * item["average_price"]

            # 米国株なら円換算
            if ticker.endswith(".T") is False and ticker != "7272":
                usdjpy = market_data["JPY=X"]["price"]
                amount *= usdjpy

        # 投資信託
        elif "units" in item and "average_price" in item:

            amount = item["units"] * item["average_price"] / 10000

        else:
            continue

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
