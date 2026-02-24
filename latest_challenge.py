"""
Resolve the latest GeoGuessr challenge ID from GitHub Gist (workflow state) or Slack channel history.
Used so we don't need to paste challenge IDs: Gist has it after each run; Slack has it in the last posted link.
"""
import os
import re
import sys
from typing import Optional

# GeoGuessr challenge/results URL pattern; capture the ID (alphanumeric)
GEOGUESSR_ID_PATTERN = re.compile(
    r"https?://(?:www\.)?geoguessr\.com/(?:challenge|results)/([A-Za-z0-9_-]+)"
)


def _get_from_gist() -> Optional[str]:
    """Latest challenge ID from GitHub Gist state (set by workflow after each run)."""
    gist_id = os.getenv("GIST_ID")
    token = os.getenv("GH_TOKEN")
    if not gist_id or not token:
        return None
    try:
        from state_storage import load_state
        state = load_state()
        return (state.get("last_challenge_id") or "").strip() or None
    except Exception:
        return None


def _get_from_slack() -> Optional[str]:
    """Latest challenge ID from the most recent GeoGuessr link in the Slack channel."""
    token = os.getenv("SLACK_BOT_TOKEN")
    channel = os.getenv("SLACK_CHANNEL_ID")
    if not token or not channel:
        return None
    try:
        from geoguessr_mcp_server import SlackClient
        slack = SlackClient(token)
        messages = slack.list_channel_messages(channel, limit=50)
        for msg in messages:
            text = msg.get("text") or ""
            blocks = msg.get("blocks") or []
            for block in blocks:
                if block.get("type") == "section":
                    section_text = (block.get("text") or {}).get("text") or ""
                    text += " " + section_text
                for elem in block.get("elements") or []:
                    elem_text = (elem.get("text") or {}).get("text") or ""
                    url = elem.get("url") or ""
                    text += " " + elem_text + " " + url
            match = GEOGUESSR_ID_PATTERN.search(text)
            if match:
                return match.group(1)
        return None
    except Exception as e:
        if sys.stderr:
            print(f"Slack fallback failed: {e}", file=sys.stderr)
        return None


def _get_from_file() -> Optional[str]:
    """Latest challenge ID from local .daily_challenge_state file."""
    try:
        from state_storage import load_state
        state = load_state()
        return (state.get("last_challenge_id") or "").strip() or None
    except Exception:
        return None


def get_latest_challenge_id() -> Optional[str]:
    """
    Get the latest challenge ID: try GitHub Gist first, then Slack channel history, then local file.
    No need to paste anything; works after 9:00/12:00 runs (Gist) or from last Slack post (Slack).
    """
    candidate = _get_from_gist()
    if candidate:
        return candidate
    candidate = _get_from_slack()
    if candidate:
        return candidate
    return _get_from_file()
