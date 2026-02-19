#!/usr/bin/env python3
"""
GeoGuessr MCP Server
Integrates GeoGuessr Daily Challenge API with MCP protocol
Uses FastMCP for easier implementation
"""

import os
import json
import requests
from datetime import datetime
from typing import Any, Optional
from dotenv import load_dotenv

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    # Fallback to basic MCP if FastMCP not available
    import sys
    import json as json_module
    
    class FastMCP:
        def __init__(self, name: str):
            self.name = name
            self.tools = []
        
        def tool(self, name: str = None, description: str = None):
            def decorator(func):
                tool_name = name or func.__name__
                self.tools.append({
                    "name": tool_name,
                    "description": description or func.__doc__,
                    "func": func
                })
                return func
            return decorator
        
        def run(self):
            # Basic stdio MCP implementation
            for line in sys.stdin:
                try:
                    message = json_module.loads(line.strip())
                    if message.get("method") == "tools/list":
                        response = {
                            "jsonrpc": "2.0",
                            "id": message.get("id"),
                            "result": {
                                "tools": [
                                    {
                                        "name": tool["name"],
                                        "description": tool["description"],
                                        "inputSchema": {"type": "object", "properties": {}}
                                    }
                                    for tool in self.tools
                                ]
                            }
                        }
                        print(json_module.dumps(response))
                        sys.stdout.flush()
                    elif message.get("method") == "tools/call":
                        tool_name = message.get("params", {}).get("name")
                        arguments = message.get("params", {}).get("arguments", {})
                        for tool in self.tools:
                            if tool["name"] == tool_name:
                                result = tool["func"](**arguments)
                                response = {
                                    "jsonrpc": "2.0",
                                    "id": message.get("id"),
                                    "result": {
                                        "content": [{"type": "text", "text": json_module.dumps(result)}]
                                    }
                                }
                                print(json_module.dumps(response))
                                sys.stdout.flush()
                                break
                except Exception as e:
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": message.get("id") if 'message' in locals() else None,
                        "error": {"code": -32603, "message": str(e)}
                    }
                    print(json_module.dumps(error_response))
                    sys.stdout.flush()

# Load environment variables
load_dotenv()

# GeoGuessr API base URL
GEOGUESSR_API_BASE = "https://www.geoguessr.com/api/v3"

# Get credentials from environment
GEOGUESSR_COOKIE = os.getenv("GEOGUESSR_COOKIE")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")

# Lazy import for browser automation (playwright optional at server start)
def _create_challenge_via_browser(**kwargs):
    from create_challenge_browser import create_challenge_via_browser as _impl
    return _impl(**kwargs)

# Initialize MCP server
mcp = FastMCP("GeoGuessr Daily Challenge")


class GeoGuessrClient:
    """Client for GeoGuessr API"""
    
    def __init__(self, cookie: str):
        self.cookie = cookie
        self.session = requests.Session()
        self.session.headers.update({
            "Cookie": f"_ncfa={cookie}",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json",
        })
    
    def validate_cookie(self) -> tuple[bool, str]:
        """Validate that the cookie is valid and authorized"""
        try:
            # Try to get daily challenge - this validates the cookie works
            # If cookie is invalid, this will fail with 401/403
            url = f"{GEOGUESSR_API_BASE}/challenges/daily-challenges/today"
            response = self.session.get(url)
            
            if response.status_code == 200:
                # Cookie is valid - try to get user info if possible
                try:
                    user_url = f"{GEOGUESSR_API_BASE}/accounts/profile"
                    user_resp = self.session.get(user_url)
                    if user_resp.status_code == 200:
                        user_data = user_resp.json()
                        user_nick = user_data.get("nick", "Unknown")
                        is_pro = user_data.get("isProUser", False)
                        return True, f"Valid cookie for user: {user_nick} (Pro: {is_pro})"
                except:
                    pass
                return True, "Cookie is valid and authorized"
            elif response.status_code == 401:
                return False, "Cookie expired or invalid (401 Unauthorized)"
            elif response.status_code == 403:
                return False, "Cookie not authorized (403 Forbidden)"
            else:
                return False, f"Cookie validation failed (Status: {response.status_code})"
        except Exception as e:
            return False, f"Cookie validation error: {str(e)}"
    
    def get_today_challenge(self) -> dict:
        """Get today's daily challenge"""
        url = f"{GEOGUESSR_API_BASE}/challenges/daily-challenges/today"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def get_previous_challenges(self, limit: int = 10) -> list:
        """Get previous daily challenges"""
        url = f"{GEOGUESSR_API_BASE}/challenges/daily-challenges/previous"
        params = {"limit": limit}
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_challenge_details(self, challenge_id: str) -> dict:
        """Get details for a specific challenge"""
        url = f"{GEOGUESSR_API_BASE}/challenges/{challenge_id}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()

    def ensure_played_challenge(self, challenge_id: str) -> None:
        """GeoGuessr only returns highscores for a challenge if the requesting user has played it.
        Start a game and submit timed-out guesses for each round so highscores become available."""
        start_url = f"{GEOGUESSR_API_BASE}/challenges/{challenge_id}"
        start_resp = self.session.post(start_url)
        if start_resp.status_code != 200:
            return
        try:
            game_token = start_resp.json().get("token")
        except Exception:
            return
        if not game_token:
            return
        for _ in range(100):
            self.session.get(f"{GEOGUESSR_API_BASE}/games/{game_token}?client=web")
            submit = self.session.post(
                f"{GEOGUESSR_API_BASE}/games/{game_token}",
                json={"lat": 0, "lng": 0, "timedOut": True, "token": game_token},
            )
            if submit.status_code != 200:
                break

    def get_challenge_highscores(self, challenge_id: str, limit: int = 26, min_rounds: int = 5) -> list:
        """Get highscores for a challenge. Returns list of {nick, totalScore, totalTime}.
        API returns items with structure: item['game']['player'] has nick, totalScore, totalTime, guesses.
        Note: GeoGuessr only returns data if the requesting user has played the challenge; call ensure_played_challenge first if needed."""
        url = f"{GEOGUESSR_API_BASE}/results/highscores/{challenge_id}"
        params = {"friends": "false", "limit": limit, "minRounds": min_rounds}
        response = self.session.get(url, params=params)
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
                total_time = pl.get("totalTime") if pl.get("totalTime") is not None else sum(g.get("time", 0) for g in guesses)
                nick = pl.get("nick") or pl.get("playerName") or game.get("playerName") or item.get("playerName") or "Unknown"
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

    def create_party(self, map_id: str = None, map_slug: str = "world", round_count: int = 5, time_limit: int = 120) -> dict:
        """Create a private party using v4 API
        
        Args:
            map_id: Map ID (optional)
            map_slug: Map slug (default: "world")
            round_count: Number of rounds (default: 5)
            time_limit: Time limit per round in seconds (default: 120 = 2 minutes)
        
        Returns:
            Party data with shareLink
        """
        url = f"https://www.geoguessr.com/api/v4/parties"
        payload = {}
        
        if map_id:
            payload["map"] = map_id
        else:
            payload["mapSlug"] = map_slug
        
        if round_count:
            payload["roundCount"] = round_count
        if time_limit:
            payload["timeLimit"] = time_limit
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def create_infinity_challenge(self, map_id: str = None, map_slug: str = "world") -> dict:
        """Create an infinity challenge using v4 API
        
        Args:
            map_id: Map ID (optional)
            map_slug: Map slug (default: "world")
        
        Returns:
            Challenge data with id
        """
        url = f"https://www.geoguessr.com/api/v4/games/infinity/challenge/new"
        payload = {}
        
        if map_id:
            payload["map"] = map_id
        else:
            payload["mapSlug"] = map_slug
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    def create_custom_challenge(self, map_id: str, time_limit: int = 120, move_limit: int = 0, access_level: int = 1) -> dict:
        """Create a custom challenge with specified time limit (in seconds)
        
        Args:
            map_id: Map ID to use for the challenge
            time_limit: Time limit per round in seconds (default: 120 = 2 minutes)
            move_limit: Move limit (0 = unlimited)
            access_level: Access level (0 = public, 1 = private/invite-only)
        
        Returns:
            Challenge data with token
        """
        url = f"{GEOGUESSR_API_BASE}/challenges"
        
        # Try multiple payload formats as API may have changed. allowGuests: False = require login.
        payloads_to_try = [
            # Format 1: With rounds, accessLevel, allowGuests
            {
                "map": map_id,
                "rounds": 5,
                "timeLimit": time_limit,
                "forbidMoving": False,
                "forbidRotating": False,
                "forbidZooming": False,
                "accessLevel": access_level,
                "allowGuests": False,
            },
            # Format 2: With roundCount
            {
                "map": map_id,
                "roundCount": 5,
                "timeLimit": time_limit,
                "forbidMoving": False,
                "forbidRotating": False,
                "forbidZooming": False,
                "accessLevel": access_level,
                "allowGuests": False,
            },
            # Format 3: Minimal with accessLevel
            {
                "map": map_id,
                "rounds": 5,
                "timeLimit": time_limit,
                "accessLevel": access_level,
                "allowGuests": False,
            },
            # Format 4: Without accessLevel (public)
            {
                "map": map_id,
                "rounds": 5,
                "timeLimit": time_limit,
                "forbidMoving": False,
                "forbidRotating": False,
                "forbidZooming": False,
                "allowGuests": False,
            },
        ]
        
        if move_limit > 0:
            for payload in payloads_to_try:
                payload["moveLimit"] = move_limit
        
        # Try each payload format
        last_error = None
        for i, payload in enumerate(payloads_to_try, 1):
            try:
                response = self.session.post(url, json=payload)
                if response.status_code in [200, 201]:
                    return response.json()
                elif response.status_code == 400:
                    error_data = response.json() if response.text else {}
                    last_error = error_data.get("message", "InvalidParameters")
                    # Continue to next format
                    continue
                else:
                    response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                last_error = str(e)
                continue
        
        # If all formats failed, raise an error with helpful message
        raise Exception(
            f"Failed to create challenge via API. Last error: {last_error}. "
            "GeoGuessr may require creating challenges through the web interface. "
            "Please create the challenge manually at https://www.geoguessr.com/challenge "
            "and share the URL."
        )


class SlackClient:
    """Client for Slack API"""
    
    def __init__(self, bot_token: str):
        self.bot_token = bot_token
        self.base_url = "https://slack.com/api"
        self.headers = {
            "Authorization": f"Bearer {bot_token}",
            "Content-Type": "application/json",
        }
    
    def post_message(self, channel: str, text: str, blocks: Optional[list] = None) -> dict:
        """Post a message to a Slack channel"""
        url = f"{self.base_url}/chat.postMessage"
        payload = {
            "channel": channel,
            "text": text,
        }
        if blocks:
            payload["blocks"] = blocks
        
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        return response.json()

    def auth_test(self) -> dict:
        """Get bot user ID (and team, etc.)."""
        r = requests.get(f"{self.base_url}/auth.test", headers=self.headers)
        r.raise_for_status()
        data = r.json()
        if not data.get("ok"):
            raise RuntimeError(data.get("error", "auth.test failed"))
        return data

    def list_channel_messages(self, channel: str, limit: int = 100) -> list:
        """List recent messages in a channel (requires channels:history scope)."""
        url = f"{self.base_url}/conversations.history"
        out = []
        cursor = None
        while True:
            payload = {"channel": channel, "limit": min(limit - len(out), 200)}
            if cursor:
                payload["cursor"] = cursor
            r = requests.get(url, headers=self.headers, params=payload)
            r.raise_for_status()
            data = r.json()
            if not data.get("ok"):
                raise RuntimeError(data.get("error", "conversations.history failed"))
            msgs = data.get("messages") or []
            out.extend(msgs)
            cursor = data.get("response_metadata", {}).get("next_cursor")
            if not cursor or len(out) >= limit:
                break
        return out

    def delete_message(self, channel: str, ts: str) -> dict:
        """Delete a message (bot can only delete its own messages)."""
        r = requests.post(
            f"{self.base_url}/chat.delete",
            headers=self.headers,
            json={"channel": channel, "ts": ts},
        )
        r.raise_for_status()
        return r.json()

    def delete_all_bot_messages(self, channel: str) -> int:
        """Delete all messages in the channel that were posted by this bot. Returns count deleted."""
        auth = self.auth_test()
        bot_user_id = auth.get("user_id")
        if not bot_user_id:
            return 0
        messages = self.list_channel_messages(channel, limit=500)
        deleted = 0
        for msg in messages:
            if msg.get("user") == bot_user_id or msg.get("bot_id"):
                try:
                    self.delete_message(channel, msg["ts"])
                    deleted += 1
                except Exception:
                    pass
        return deleted


def format_challenge_message(challenge_data: dict, custom_time_limit: int = None, leaderboard_data: list = None, actual_time_limit: int = None, rounds: int = 5, today_date: str = "", yesterday_date: str = "") -> tuple[str, list]:
    """Format challenge data into Slack message"""
    # Use token if challengeId is not available (daily challenge uses token)
    challenge_id = challenge_data.get("challengeId") or challenge_data.get("token", "")
    map_name = challenge_data.get("mapName", "Daily Challenge")
    time_limit = custom_time_limit if custom_time_limit is not None else challenge_data.get("timeLimit", 0)
    move_limit = challenge_data.get("moveLimit", 0)
    
    # Format time limit - show desired per-round time if specified
    if custom_time_limit:
        time_str = f"{custom_time_limit // 60} minutes per round"
        total_time = custom_time_limit * rounds
        time_str += f" ({total_time // 60} minutes total)"
    elif time_limit:
        minutes = time_limit // 60
        seconds = time_limit % 60
        time_str = f"{minutes}m {seconds}s total" if minutes else f"{seconds}s total"
    else:
        time_str = "No time limit"
    
    # Create challenge URL
    if not challenge_id:
        challenge_url = "https://www.geoguessr.com/challenge"
    else:
        challenge_url = f"https://www.geoguessr.com/challenge/{challenge_id}"
    
    # Build title with date
    title = "🌍 GeoGuessr Daily Challenge"
    if today_date:
        title += f" ({today_date})"
    
    # Build text message
    text = f"{title}!\n\nMap: {map_name}\nTime: {time_str}\nRounds: {rounds}\nMoves: {move_limit if move_limit else 'Unlimited'}\n\nPlay here: {challenge_url}"
    
    # Add leaderboard if provided (only show if there are actual team results)
    if leaderboard_data and len(leaderboard_data) > 0:
        results_header = "📊 Yesterday's Top Results"
        if yesterday_date:
            results_header += f" ({yesterday_date})"
        text += f"\n\n{results_header}:"
        for i, entry in enumerate(leaderboard_data[:10], 1):  # Top 10
            nick = entry.get("nick", "Unknown")
            score = entry.get("totalScore", 0)
            time_sec = entry.get("totalTime", 0)
            text += f"\n{i}. {nick} - Score: {score:,} | Time: {time_sec}s"
    
    # Build title with date
    header_title = "🌍 GeoGuessr Daily Challenge"
    if today_date:
        header_title += f" ({today_date})"
    
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": header_title
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Map:*\n{map_name}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Time Limit:*\n{time_str}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Rounds:*\n{rounds}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Move Limit:*\n{move_limit if move_limit else 'Unlimited'}"
                }
            ]
        }
    ]
    
    # Add leaderboard section if provided (only show if there are actual team results)
    if leaderboard_data and len(leaderboard_data) > 0:
        results_header = "*📊 Yesterday's Top Results*"
        if yesterday_date:
            results_header += f" ({yesterday_date})"
        results_header += ":*\n"
        
        leaderboard_text = results_header
        for i, entry in enumerate(leaderboard_data[:10], 1):  # Top 10
            nick = entry.get("nick", "Unknown")
            score = entry.get("totalScore", 0)
            time_sec = entry.get("totalTime", 0)
            leaderboard_text += f"{i}. *{nick}* - {score:,} pts | {time_sec}s\n"
        
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": leaderboard_text
            }
        })
    
    # Add play button
    blocks.append({
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": "Play Challenge"
                },
                "url": challenge_url,
                "style": "primary"
            }
        ]
    })
    
    return text, blocks


def format_softhouse_daily(
    challenge_url: str,
    map_name: str,
    time_str: str,
    rounds: int,
    move_limit: int,
    today_date: str,
    leaderboard_data: list,
    challenge_number: int = 1,
    results_date_str: str = "",
) -> tuple[str, list]:
    """Format Softhouse daily challenge message. challenge_number is always shown (#1 or #2). Results section uses results_date_str for 'Previous challenge results (DD/MM/YYYY)'."""
    header_title = f"GeoGuessr - Softhouse Daily Challenge {today_date} #{challenge_number}"
    text = f"{header_title}\n\nMap: {map_name}\nTime: {time_str}\nRounds: {rounds}\nMoves: {move_limit if move_limit else 'Unlimited'}\n\nPlay here: {challenge_url}"
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": header_title},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Map:*\n{map_name}"},
                {"type": "mrkdwn", "text": f"*Time Limit:*\n{time_str}"},
                {"type": "mrkdwn", "text": f"*Rounds:*\n{rounds}"},
                {"type": "mrkdwn", "text": f"*Move Limit:*\n{move_limit if move_limit else 'Unlimited'}"},
            ],
        },
    ]
    if leaderboard_data and len(leaderboard_data) > 0:
        # Aligned columns: Rank (4), Name (20), Result (8), Time(s) (6) — in monospace code block
        W_RANK, W_NAME, W_RESULT, W_TIME = 4, 20, 8, 6
        header_line = "Rank".center(W_RANK) + " | " + "Name".ljust(W_NAME) + " | " + "Result".rjust(W_RESULT) + " | " + "Time(s)".rjust(W_TIME)
        sep_line = "-" * W_RANK + "-+-" + "-" * W_NAME + "-+-" + "-" * W_RESULT + "-+-" + "-" * W_TIME
        table_lines = [header_line, sep_line]
        for i, entry in enumerate(leaderboard_data[:10], 1):
            nick = (entry.get("nick") or "Unknown")[:W_NAME].ljust(W_NAME)
            score_str = f"{entry.get('totalScore', 0):,}".rjust(W_RESULT)
            time_str = str(entry.get("totalTime", 0)).rjust(W_TIME)
            table_lines.append(str(i).rjust(W_RANK) + " | " + nick + " | " + score_str + " | " + time_str)
        table_block = "```\n" + "\n".join(table_lines) + "\n```"
        results_title = "*📊 Previous challenge results*"
        if results_date_str:
            results_title += f" ({results_date_str})"
        results_title += "*"
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": results_title + "\n" + table_block},
        })
    blocks.append({
        "type": "actions",
        "elements": [{"type": "button", "text": {"type": "plain_text", "text": "Play Challenge"}, "url": challenge_url, "style": "primary"}],
    })
    if leaderboard_data and len(leaderboard_data) > 0:
        W_RANK, W_NAME, W_RESULT, W_TIME = 4, 20, 8, 6
        header_line = "Rank".center(W_RANK) + " | " + "Name".ljust(W_NAME) + " | " + "Result".rjust(W_RESULT) + " | " + "Time(s)".rjust(W_TIME)
        sep_line = "-" * W_RANK + "-+-" + "-" * W_NAME + "-+-" + "-" * W_RESULT + "-+-" + "-" * W_TIME
        text += f"\n\n📊 Previous challenge results ({results_date_str or 'previous'}):\n"
        text += header_line + "\n" + sep_line + "\n"
        for i, entry in enumerate(leaderboard_data[:10], 1):
            nick = (entry.get("nick") or "Unknown")[:W_NAME].ljust(W_NAME)
            text += str(i).rjust(W_RANK) + " | " + nick + " | " + f"{entry.get('totalScore', 0):,}".rjust(W_RESULT) + " | " + str(entry.get("totalTime", 0)).rjust(W_TIME) + "\n"
    return text, blocks


def format_results_only_message(leaderboard_data: list, results_date_str: str = "", challenge_id: str = "") -> tuple[str, list]:
    """Format a Slack message with only the results table (no challenge link)."""
    if not leaderboard_data or len(leaderboard_data) == 0:
        return "", []
    W_RANK, W_NAME, W_RESULT, W_TIME = 4, 20, 8, 6
    header_line = "Rank".center(W_RANK) + " | " + "Name".ljust(W_NAME) + " | " + "Result".rjust(W_RESULT) + " | " + "Time(s)".rjust(W_TIME)
    sep_line = "-" * W_RANK + "-+-" + "-" * W_NAME + "-+-" + "-" * W_RESULT + "-+-" + "-" * W_TIME
    table_lines = [header_line, sep_line]
    for i, entry in enumerate(leaderboard_data[:15], 1):
        nick = (entry.get("nick") or "Unknown")[:W_NAME].ljust(W_NAME)
        score_str = f"{entry.get('totalScore', 0):,}".rjust(W_RESULT)
        time_str = str(entry.get("totalTime", 0)).rjust(W_TIME)
        table_lines.append(str(i).rjust(W_RANK) + " | " + nick + " | " + score_str + " | " + time_str)
    table_block = "```\n" + "\n".join(table_lines) + "\n```"
    results_title = "*📊 Challenge Results*"
    if results_date_str:
        results_title += f" ({results_date_str})"
    if challenge_id:
        results_title += f" - Challenge: `{challenge_id}`"
    results_title += "*"
    text = results_title + "\n" + table_block
    blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": results_title + "\n" + table_block}}]
    return text, blocks


# MCP Tools
@mcp.tool()
def get_today_challenge() -> dict:
    """Get today's GeoGuessr daily challenge information"""
    if not GEOGUESSR_COOKIE:
        raise ValueError("GEOGUESSR_COOKIE environment variable not set")
    
    client = GeoGuessrClient(GEOGUESSR_COOKIE)
    return client.get_today_challenge()


@mcp.tool()
def get_previous_challenges(limit: int = 10) -> list:
    """Get previous GeoGuessr daily challenges"""
    if not GEOGUESSR_COOKIE:
        raise ValueError("GEOGUESSR_COOKIE environment variable not set")
    
    client = GeoGuessrClient(GEOGUESSR_COOKIE)
    return client.get_previous_challenges(limit)


@mcp.tool()
def post_challenge_to_slack(channel_id: Optional[str] = None) -> dict:
    """Get today's challenge and post it to Slack"""
    if not GEOGUESSR_COOKIE:
        raise ValueError("GEOGUESSR_COOKIE environment variable not set")
    if not SLACK_BOT_TOKEN:
        raise ValueError("SLACK_BOT_TOKEN environment variable not set")
    
    target_channel = channel_id or SLACK_CHANNEL_ID
    if not target_channel:
        raise ValueError("Slack channel ID not provided and SLACK_CHANNEL_ID not set")
    
    # Get today's challenge
    geoguessr = GeoGuessrClient(GEOGUESSR_COOKIE)
    challenge = geoguessr.get_today_challenge()
    
    # Format and post to Slack
    slack = SlackClient(SLACK_BOT_TOKEN)
    text, blocks = format_challenge_message(challenge)
    result = slack.post_message(target_channel, text, blocks)
    
    challenge_url = f"https://www.geoguessr.com/challenge/{challenge.get('challengeId', '')}"
    
    return {
        "success": True,
        "challenge_url": challenge_url,
        "slack_response": result
    }


@mcp.tool()
def get_challenge_details(challenge_id: str) -> dict:
    """Get detailed information about a specific challenge"""
    if not GEOGUESSR_COOKIE:
        raise ValueError("GEOGUESSR_COOKIE environment variable not set")
    
    client = GeoGuessrClient(GEOGUESSR_COOKIE)
    return client.get_challenge_details(challenge_id)


@mcp.tool()
def create_challenge(
    map_slug: str = "world",
    rounds: int = 5,
    time_per_round: int = 90,
    cookie: Optional[str] = None,
    email: Optional[str] = None,
    password: Optional[str] = None,
    post_to_slack: bool = False,
    channel_id: Optional[str] = None,
) -> dict:
    """Create a GeoGuessr challenge via browser automation.

    Auth (use one): pass cookie (_ncfa), or set GEOGUESSR_COOKIE in .env, or pass
    both email and password to log in via the sign-in form.

    Requires Playwright: pip install playwright && playwright install chromium.

    Returns the challenge URL on success. If post_to_slack is True and Slack is
    configured, also posts the challenge to the given channel (or default)."""
    use_credentials = email and password
    if not use_credentials and not (cookie or GEOGUESSR_COOKIE):
        raise ValueError(
            "Provide cookie (or GEOGUESSR_COOKIE) or both email and password."
        )
    result = _create_challenge_via_browser(
        map_slug=map_slug,
        rounds=rounds,
        time_per_round=time_per_round,
        headed=False,
        slow_mo=0,
        cookie=cookie,
        email=email if use_credentials else None,
        password=password if use_credentials else None,
    )
    if result is None:
        return {
            "success": False,
            "error": "Browser automation did not produce a challenge URL. Run with headed=True locally to debug.",
        }
    url, session_cookie = result if isinstance(result, tuple) else (result, None)
    auth = session_cookie or cookie or GEOGUESSR_COOKIE
    out = {"success": True, "challenge_url": url}
    if post_to_slack and SLACK_BOT_TOKEN:
        target = channel_id or SLACK_CHANNEL_ID
        if not target:
            out["slack_posted"] = False
            out["slack_error"] = "No channel_id and SLACK_CHANNEL_ID not set"
            return out
        try:
            challenge_id = url.rstrip("/").split("/challenge/")[-1].split("?")[0]
            client = GeoGuessrClient(auth)
            details = client.get_challenge_details(challenge_id)
            slack = SlackClient(SLACK_BOT_TOKEN)
            text, blocks = format_challenge_message(details)
            slack.post_message(target, text, blocks)
            out["slack_posted"] = True
            out["channel_id"] = target
        except Exception as e:
            out["slack_posted"] = False
            out["slack_error"] = str(e)
    elif post_to_slack:
        out["slack_posted"] = False
        out["slack_error"] = "SLACK_BOT_TOKEN not set"
    return out


if __name__ == "__main__":
    mcp.run()
