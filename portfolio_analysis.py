import json


def calculate_portfolio_impact(portfolio, market_data):

    results = []

    for item in portfolio["holdings"]:

        ticker = item["ticker"]
        amount = item["amount_yen"]

        if ticker in market_data:

            change = market_data[ticker].get("change_percent")

            if change is not None:

                impact = amount * (change / 100)

                results.append({
                    "ticker": ticker,
                    "name": item["name"],
                    "amount_yen": amount,
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
