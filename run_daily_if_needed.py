#!/usr/bin/env python3
"""
Run the Softhouse daily challenge hourly from 8:00 to 15:00 on weekdays (Mon-Fri).
If the machine was asleep, runs the first time it wakes and the scheduler fires.
Used by launchd; runs hourly and checks weekday/hour constraints.
"""
import subprocess
import sys
from pathlib import Path
from datetime import datetime

root = Path(__file__).resolve().parent
PYTHON = root / "venv" / "bin" / "python"
SCRIPT = root / "daily_softhouse_challenge.py"


def main() -> int:
    now = datetime.now()
    weekday = now.weekday()  # 0=Monday, 6=Sunday
    
    # Only run on weekdays (Monday=0 to Friday=4)
    if weekday >= 5:  # Saturday (5) or Sunday (6)
        return 0
    
    # Only run between 8:00 and 15:00 (8am to 3pm)
    if now.hour < 8 or now.hour >= 15:
        return 0
    
    # Run the challenge script (it handles state management internally)
    result = subprocess.run(
        [str(PYTHON), str(SCRIPT)],
        cwd=str(root),
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
