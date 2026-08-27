"""
Posts "N / 365" to a Telegram channel, where N is calculated automatically
from a fixed start date (day 1). Meant to be run once a day by a scheduler
(GitHub Actions, cron, etc.) — no manual incrementing needed.

Required environment variables:
  BOT_TOKEN    - Telegram bot token from BotFather
  CHANNEL_ID   - Telegram channel id or @username (e.g. @LeetCodeJourney or -1001234567890)
  START_DATE   - the date that should count as "Day 1", format YYYY-MM-DD

Optional environment variables:
  TOTAL_DAYS   - denominator in the "N / TOTAL_DAYS" message (default: 365)
"""

import os
import sys
from datetime import date, datetime

import requests

STATE_FILE = "last_posted_day.txt"


def get_env(name: str, required: bool = True, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if required and not value:
        print(f"Missing required environment variable: {name}", file=sys.stderr)
        sys.exit(1)
    return value


def compute_day_number(start_date: date, today: date) -> int:
    return (today - start_date).days + 1


def read_last_posted_day() -> int | None:
    if not os.path.exists(STATE_FILE):
        return None
    try:
        with open(STATE_FILE, "r") as f:
            return int(f.read().strip())
    except (ValueError, OSError):
        return None


def write_last_posted_day(day_number: int) -> None:
    with open(STATE_FILE, "w") as f:
        f.write(str(day_number))


def main() -> None:
    bot_token = get_env("BOT_TOKEN")
    channel_id = get_env("CHANNEL_ID")
    start_date_str = get_env("START_DATE")
    total_days = int(get_env("TOTAL_DAYS", required=False, default="365"))

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    except ValueError:
        print(f"START_DATE must be in YYYY-MM-DD format, got: {start_date_str}", file=sys.stderr)
        sys.exit(1)

    today = date.today()
    day_number = compute_day_number(start_date, today)

    if day_number < 1:
        print(f"START_DATE ({start_date}) is in the future relative to today ({today}); nothing to post yet.")
        sys.exit(0)

    last_posted = read_last_posted_day()
    if last_posted is not None and day_number <= last_posted:
        print(f"Day {day_number} was already posted (last posted: {last_posted}). Skipping to avoid a duplicate.")
        sys.exit(0)

    message = f"{day_number} / {total_days}"

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    response = requests.post(url, data={"chat_id": channel_id, "text": message}, timeout=15)

    if response.status_code != 200:
        print(f"Telegram API error ({response.status_code}): {response.text}", file=sys.stderr)
        sys.exit(1)

    write_last_posted_day(day_number)
    print(f"Posted '{message}' to {channel_id} successfully.")


if __name__ == "__main__":
    main()
