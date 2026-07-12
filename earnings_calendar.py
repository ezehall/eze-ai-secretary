import datetime


def get_upcoming_earnings():

    # 仮データ
    # 後でAPI取得に変更

    earnings = [
        {
            "ticker": "NVDA",
            "name": "NVIDIA",
            "date": "2026-08-20",
            "importance": "★★★★★"
        },
        {
            "ticker": "GOOGL",
            "name": "Alphabet",
            "date": "2026-07-28",
            "importance": "★★★★"
        }
    ]

    today = datetime.date.today()

    upcoming = []

    for item in earnings:
        date = datetime.date.fromisoformat(item["date"])

        diff = (date - today).days

        if 0 <= diff <= 14:
            item["days_left"] = diff
            upcoming.append(item)

    return upcoming
