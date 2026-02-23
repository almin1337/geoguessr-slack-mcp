"""
Shared logic to fetch GeoGuessr challenge leaderboard by challenge ID.
Used by fetch_challenge_results.py and daily_softhouse_challenge.py so both use the same approach:
try highscores API first (works for public challenges), then ensure_played_challenge + retry if needed.
Returns list of {"nick", "totalScore", "totalTime"} sorted by score desc, time asc.
"""
import requests

GEOGUESSR_API_BASE = "https://www.geoguessr.com/api/v3"


def _session(cookie: str) -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "Cookie": f"_ncfa={cookie}",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/json",
    })
    return s


def _ensure_played_challenge(session: requests.Session, challenge_id: str) -> None:
    start_resp = session.post(f"{GEOGUESSR_API_BASE}/challenges/{challenge_id}")
    if start_resp.status_code != 200:
        return
    try:
        game_token = start_resp.json().get("token")
    except Exception:
        return
    if not game_token:
        return
    for _ in range(10):
        session.get(f"{GEOGUESSR_API_BASE}/games/{game_token}?client=web")
        r = session.post(
            f"{GEOGUESSR_API_BASE}/games/{game_token}",
            json={"lat": 0, "lng": 0, "timedOut": True, "token": game_token},
        )
        if r.status_code != 200:
            break


def _get_highscores(session: requests.Session, challenge_id: str, limit: int = 26, min_rounds: int = 5) -> list:
    url = f"{GEOGUESSR_API_BASE}/results/highscores/{challenge_id}"
    params = {"friends": "false", "limit": limit, "minRounds": min_rounds}
    response = session.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    items = data.get("items") or []
    out = []
    for item in items:
        try:
            game = item.get("game") or {}
            pl = game.get("player") or {}
            guesses = pl.get("guesses") or []
            if not guesses:
                continue
            timed_out_all = all(g.get("timedOut") for g in guesses)
            if timed_out_all:
                continue
            total_time = (
                pl.get("totalTime")
                if pl.get("totalTime") is not None
                else sum(g.get("time", 0) for g in guesses)
            )
            nick = (
                pl.get("nick")
                or pl.get("playerName")
                or game.get("playerName")
                or item.get("playerName")
                or "Unknown"
            )
            score_val = pl.get("totalScore", 0)
            if isinstance(score_val, dict):
                score_val = score_val.get("amount", 0) or 0
            out.append({
                "nick": nick,
                "totalScore": int(score_val) if score_val is not None else 0,
                "totalTime": int(total_time) if total_time is not None else 0,
            })
        except (KeyError, TypeError):
            continue
    out.sort(key=lambda x: (-x["totalScore"], x["totalTime"]))
    return out


def get_leaderboard_for_challenge(cookie: str, challenge_id: str) -> list:
    """
    Fetch leaderboard for a challenge by ID. Same approach as fetch_challenge_results.py:
    try highscores first (works for public challenges), then ensure_played + highscores if empty.
    Returns list of {"nick", "totalScore", "totalTime"}.
    """
    session = _session(cookie)
    try:
        lb = _get_highscores(session, challenge_id)
    except Exception:
        lb = []
    if not lb:
        _ensure_played_challenge(session, challenge_id)
        try:
            lb = _get_highscores(session, challenge_id)
        except Exception:
            lb = []
    return lb
