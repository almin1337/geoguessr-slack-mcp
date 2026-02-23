#!/usr/bin/env python3
"""Fetch and print leaderboard for a GeoGuessr challenge. Usage: python fetch_challenge_results.py <challenge_id>"""
import os
import sys
from pathlib import Path

# Load .env manually (no dotenv required)
root = Path(__file__).resolve().parent
env_file = root / ".env"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ[k.strip()] = v.strip().strip('"').strip("'")

from challenge_results import get_leaderboard_for_challenge


def main():
    if len(sys.argv) < 2:
        print("Usage: python fetch_challenge_results.py <challenge_id>", file=sys.stderr)
        sys.exit(1)
    cid = sys.argv[1].strip()
    cookie = os.getenv("GEOGUESSR_COOKIE")
    if not cookie:
        print("GEOGUESSR_COOKIE not set in .env", file=sys.stderr)
        sys.exit(1)
    lb = get_leaderboard_for_challenge(cookie, cid)
    if not lb:
        print("No results found for this challenge.")
        return
    W_RANK, W_NAME, W_SCORE, W_TIME = 4, 20, 8, 8
    print("Leaderboard for Challenge:", cid)
    print("Total Players:", len(lb))
    print()
    header = "Rank".ljust(W_RANK) + " | " + "Player Name".ljust(W_NAME) + " | " + "Score".rjust(W_SCORE) + " | " + "Time (s)".rjust(W_TIME)
    sep = "-" * W_RANK + "-+-" + "-" * W_NAME + "-+-" + "-" * W_SCORE + "-+-" + "-" * W_TIME
    print(header)
    print(sep)
    for i, e in enumerate(lb[:15], 1):
        nick = (e.get("nick") or "Unknown")[:W_NAME].ljust(W_NAME)
        score = str(e.get("totalScore", 0)).rjust(W_SCORE)
        time_s = str(e.get("totalTime", 0)).rjust(W_TIME)
        print(str(i).rjust(W_RANK) + " | " + nick + " | " + score + " | " + time_s)


if __name__ == "__main__":
    main()
