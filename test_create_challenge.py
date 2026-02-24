#!/usr/bin/env python3
"""
Test whether the current GeoGuessr account (via GEOGUESSR_COOKIE in .env) can create a challenge.
Use this with a non-Pro account to see if challenge creation is allowed.

Usage:
  1. In .env set GEOGUESSR_COOKIE to the _ncfa cookie of the account you want to test (e.g. non-Pro).
  2. Run: python test_create_challenge.py

No challenge is saved to state; this only checks if the API accepts the create request.
"""
import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
env_path = root / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)

cookie = os.getenv("GEOGUESSR_COOKIE")
if not cookie:
    print("GEOGUESSR_COOKIE not set in .env", file=sys.stderr)
    sys.exit(1)

import requests
session = requests.Session()
session.headers.update({
    "Cookie": f"_ncfa={cookie}",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json",
    "Content-Type": "application/json",
})
base = "https://www.geoguessr.com/api/v3"

# Same payload as daily_softhouse_challenge.py (private challenge, 5 rounds, 90s)
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
    url = f"https://www.geoguessr.com/challenge/{token}" if token else None
    print("OK: Challenge creation succeeded (Pro or allowed tier).")
    if url:
        print(f"     Challenge URL: {url}")
    sys.exit(0)

# Failure: show what GeoGuessr returned
print("FAIL: Challenge creation was rejected.", file=sys.stderr)
print(f"     HTTP status: {resp.status_code}", file=sys.stderr)
try:
    body = resp.json()
    msg = body.get("message") or body.get("error") or str(body)
    print(f"     Response: {msg}", file=sys.stderr)
    if resp.status_code == 403 and "pro" in msg.lower():
        print("     → This account needs Pro to create challenges. Daily job will fail without Pro.", file=sys.stderr)
except Exception:
    print(f"     Response body (raw): {resp.text[:500]}", file=sys.stderr)
sys.exit(1)
