#!/usr/bin/env python3
"""
State storage abstraction for daily challenge state.
Supports file-based storage (local) and GitHub Gist storage (GitHub Actions).
"""
import os
import sys
import json
import requests
from pathlib import Path
from typing import Optional


def load_state() -> dict:
    """Load state: last_challenge_id, last_challenge_date (YYYY-MM-DD), challenges_today_count."""
    # Check if we're in GitHub Actions and have Gist configured
    gist_id = os.getenv("GITHUB_GIST_ID")
    github_token = os.getenv("GITHUB_TOKEN")
    
    if gist_id and github_token:
        return _load_from_gist(gist_id, github_token)
    else:
        return _load_from_file()


def save_state(last_challenge_id: str, last_challenge_date: str, challenges_today_count: int) -> None:
    """Save state after posting a challenge."""
    state_data = {
        "last_challenge_id": last_challenge_id,
        "last_challenge_date": last_challenge_date,
        "challenges_today_count": challenges_today_count,
    }
    
    # Check if we're in GitHub Actions and have Gist configured
    gist_id = os.getenv("GITHUB_GIST_ID")
    github_token = os.getenv("GITHUB_TOKEN")
    
    if gist_id and github_token:
        _save_to_gist(gist_id, github_token, state_data)
    else:
        _save_to_file(state_data)


def _load_from_file() -> dict:
    """Load state from local file."""
    root = Path(__file__).resolve().parent
    state_file = root / ".daily_challenge_state"
    if not state_file.exists():
        return {}
    try:
        return json.loads(state_file.read_text())
    except Exception:
        return {}


def _save_to_file(state_data: dict) -> None:
    """Save state to local file."""
    root = Path(__file__).resolve().parent
    state_file = root / ".daily_challenge_state"
    state_file.write_text(json.dumps(state_data, indent=2))


def _load_from_gist(gist_id: str, github_token: str) -> dict:
    """Load state from GitHub Gist."""
    try:
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        response = requests.get(f"https://api.github.com/gists/{gist_id}", headers=headers, timeout=10)
        if response.status_code == 200:
            gist_data = response.json()
            # Look for a file named "state.json" or any .json file
            files = gist_data.get("files", {})
            for filename, file_data in files.items():
                if filename.endswith(".json"):
                    content = file_data.get("content", "{}")
                    return json.loads(content)
        return {}
    except Exception:
        return {}


def _save_to_gist(gist_id: str, github_token: str, state_data: dict) -> None:
    """Save state to GitHub Gist."""
    try:
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        # Get current gist to preserve other files
        response = requests.get(f"https://api.github.com/gists/{gist_id}", headers=headers, timeout=10)
        files = {}
        if response.status_code == 200:
            existing_files = response.json().get("files", {})
            # Preserve existing files
            for filename, file_data in existing_files.items():
                if not filename.endswith(".json"):
                    files[filename] = {"content": file_data.get("content", "")}
        
        # Add or update state.json
        files["state.json"] = {"content": json.dumps(state_data, indent=2)}
        
        # Update gist
        payload = {"files": files}
        requests.patch(
            f"https://api.github.com/gists/{gist_id}",
            headers=headers,
            json=payload,
            timeout=10,
        )
    except Exception as e:
        print(f"Warning: Failed to save state to Gist: {e}", file=sys.stderr)
        # Fallback to file if in local environment
        _save_to_file(state_data)
