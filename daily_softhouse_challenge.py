#!/usr/bin/env python3
"""
Post GeoGuessr Softhouse Daily Challenge to Slack every day.
Run at 9:00 via cron. Creates a new challenge (login required), includes yesterday's results.
Title: "GeoGuessr - Softhouse Daily Challenge DD/MM/YYYY"
Results format: Rank | Name | Result | Time(s)
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Load .env from project root
root = Path(__file__).resolve().parent
env_path = root / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)

sys.path.insert(0, str(root))
from geoguessr_mcp_server import (
    GeoGuessrClient,
    SlackClient,
    format_softhouse_daily,
)

GEOGUESSR_COOKIE = os.getenv("GEOGUESSR_COOKIE")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")
STATE_FILE = root / ".daily_challenge_state"


def load_state() -> dict:
    """Load state: last_challenge_id, last_challenge_date (YYYY-MM-DD), challenges_today_count."""
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def save_state(last_challenge_id: str, last_challenge_date: str, challenges_today_count: int) -> None:
    """Save state after posting a challenge."""
    STATE_FILE.write_text(
        json.dumps(
            {
                "last_challenge_id": last_challenge_id,
                "last_challenge_date": last_challenge_date,
                "challenges_today_count": challenges_today_count,
            },
            indent=2,
        )
    )


def load_previous_challenge_id() -> str | None:
    return load_state().get("last_challenge_id")


def create_challenge_api(cookie: str) -> str | None:
    import requests
    session = requests.Session()
    session.headers.update({
        "Cookie": f"_ncfa={cookie}",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json",
    })
    base = "https://www.geoguessr.com/api/v3"
    r = session.get(f"{base}/maps/world")
    if r.status_code != 200:
        r = session.get(f"{base}/maps/a-community-world")
    map_id = r.json().get("id") if r.status_code == 200 else "62a44b22040f04bd36e8a914"
    payload = {
        "forbidMoving": False,
        "forbidRotating": False,
        "forbidZooming": False,
        "map": map_id,
        "rounds": 5,
        "timeLimit": 90,
        "accessLevel": 1,
        "allowGuests": False,
    }
    resp = session.post(f"{base}/challenges", json=payload)
    if resp.status_code in (200, 201):
        data = resp.json()
        token = data.get("token") or data.get("challengeId") or data.get("id")
        if token:
            return f"https://www.geoguessr.com/challenge/{token}"
    return None


def create_challenge_browser(cookie: str) -> str | None:
    from create_challenge_browser import create_challenge_via_browser
    result = create_challenge_via_browser(
        map_slug="world", rounds=5, time_per_round=90, cookie=cookie
    )
    if result:
        return result[0] if isinstance(result, tuple) else result
    return None


def main() -> None:
    if not GEOGUESSR_COOKIE:
        print("ERROR: GEOGUESSR_COOKIE not set", file=sys.stderr)
        sys.exit(1)
    if not SLACK_BOT_TOKEN or not SLACK_CHANNEL_ID:
        print("ERROR: SLACK_BOT_TOKEN and SLACK_CHANNEL_ID must be set", file=sys.stderr)
        sys.exit(1)

    today = datetime.now(timezone.utc)
    today_iso = today.strftime("%Y-%m-%d")
    today_str = today.strftime("%d/%m/%Y")

    state = load_state()
    prev_id = state.get("last_challenge_id")
    last_date = state.get("last_challenge_date", "")
    # This run's number for today: first of the day = 1, second = 2, ...
    if last_date == today_iso:
        challenge_number = state.get("challenges_today_count", 0) + 1
    else:
        challenge_number = 1
    # Date to show for "previous challenge results" (same day or yesterday)
    if last_date == today_iso:
        results_date_str = today_str
    elif last_date:
        try:
            results_date_str = datetime.strptime(last_date, "%Y-%m-%d").strftime("%d/%m/%Y")
        except Exception:
            results_date_str = last_date
    else:
        results_date_str = today_str

    client = GeoGuessrClient(GEOGUESSR_COOKIE)
    previous_leaderboard = []
    if prev_id:
        try:
            # GeoGuessr only returns highscores if our account has played the challenge.
            # "Play" it once (timed-out rounds) so the API exposes the scoreboard.
            client.ensure_played_challenge(prev_id)
            previous_leaderboard = client.get_challenge_highscores(prev_id)
        except Exception as e:
            print(f"Warning: could not fetch previous challenge results: {e}", file=sys.stderr)

    challenge_url = create_challenge_api(GEOGUESSR_COOKIE)
    if not challenge_url:
        print("API create failed, trying browser...", file=sys.stderr)
        challenge_url = create_challenge_browser(GEOGUESSR_COOKIE)
    if not challenge_url:
        print("ERROR: Could not create challenge", file=sys.stderr)
        sys.exit(1)

    challenge_id = challenge_url.rstrip("/").split("/challenge/")[-1].split("?")[0]
    save_state(challenge_id, today_iso, challenge_number)

    try:
        details = client.get_challenge_details(challenge_id)
        map_name = details.get("map", {}).get("name", "World")
        ch = details.get("challenge", {})
        time_limit = ch.get("timeLimit", 90)
        rounds = ch.get("roundCount", 5)
        move_limit = ch.get("moveLimit", 0)
    except Exception:
        map_name = "World"
        time_limit = 90
        rounds = 5
        move_limit = 0

    time_str = f"{time_limit // 60}m {time_limit % 60}s per round" if time_limit else "No time limit"

    text, blocks = format_softhouse_daily(
        challenge_url=challenge_url,
        map_name=map_name,
        time_str=time_str,
        rounds=rounds,
        move_limit=move_limit,
        today_date=today_str,
        challenge_number=challenge_number,
        results_date_str=results_date_str,
        leaderboard_data=previous_leaderboard,
    )

    slack = SlackClient(SLACK_BOT_TOKEN)
    result = slack.post_message(SLACK_CHANNEL_ID, text, blocks)
    if not result.get("ok"):
        print(f"ERROR: Slack post failed: {result.get('error')}", file=sys.stderr)
        sys.exit(1)
    print(f"Posted Softhouse Daily Challenge: {challenge_url}")


if __name__ == "__main__":
    main()
