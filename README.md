# GeoGuessr Slack Integration

MCP server and daily job for GeoGuessr: create challenges (login required), post to Slack, and show yesterday’s results.

## What’s included

- **geoguessr_mcp_server.py** – MCP server (get daily challenge, create challenge, post to Slack, etc.).
- **daily_softhouse_challenge.py** – Daily job: creates a new **private** challenge (login required to play), posts to Slack with title **"GeoGuessr - Softhouse Daily Challenge DD/MM/YYYY"**, and appends yesterday’s results as **Rank | Name | Result | Time(s)**.
- **create_challenge_browser.py** – Browser automation fallback when the API is unavailable (used by MCP and daily script).

## Requirements

- GeoGuessr account (Pro/Unlimited recommended for creating challenges).
- `_ncfa` cookie: log in at geoguessr.com → DevTools → Application → Cookies → copy `_ncfa`.
- Slack app with Bot Token and scopes: `channels:read`, `chat:write`, `users:read`.
- Optional: `playwright` and `playwright install chromium` for browser fallback.

## Setup

1. **Dependencies**
   ```bash
   pip install mcp requests python-dotenv playwright
   playwright install chromium   # optional, for browser fallback
   ```

2. **Environment** – create `.env` in the project root:
   ```
   GEOGUESSR_COOKIE=your_ncfa_cookie_value
   SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
   SLACK_CHANNEL_ID=C1234567890
   ```

3. **Run the MCP server**
   ```bash
   python geoguessr_mcp_server.py
   ```

See **SETUP_GUIDE.md** and **setup_slack_app.md** for Slack app setup.

## Daily Softhouse challenge at 9:00

Run **daily_softhouse_challenge.py** every day at 9:00 (e.g. with cron). It will:

1. Load the previous challenge ID from `.daily_challenge_state`.
2. Fetch yesterday’s results (Rank, Name, Result, Time(s)).
3. Create a new **private** challenge (login required; `accessLevel: 1`).
4. Post to Slack with title **"GeoGuessr - Softhouse Daily Challenge DD/MM/YYYY"** and yesterday’s results.
5. Save the new challenge ID for the next run.

**Cron example (9:00 local time):**

```bash
crontab -e
```

Add:

```
0 9 * * * cd /path/to/geoguessr-slack-mcp && /path/to/venv/bin/python daily_softhouse_challenge.py >> /tmp/geoguessr_softhouse.log 2>&1
```

Replace `/path/to/geoguessr-slack-mcp` and `/path/to/venv/bin/python` with your paths.

**Run once manually:**

```bash
python daily_softhouse_challenge.py
```

## Manual extra challenges (same day)

You can post **more than one challenge on the same day**. Challenges run automatically hourly from 8:00-15:00 on weekdays; you can also trigger manually.

**What to do for an extra challenge the same day**

1. Open a terminal.
2. Go to the project and run the same script:
   ```bash
   cd /path/to/geoguessr-slack-mcp
   ./venv/bin/python daily_softhouse_challenge.py
   ```
   (Use your actual project path; on Windows use `venv\Scripts\python.exe`.)

**Behaviour**

- **Title:** The first challenge of the day has no number. The second gets **#2**, the third **#3**, and so on (e.g. *GeoGuessr - Softhouse Daily Challenge 19/02/2026 #2*).
- **Results:** Each new post always shows results from the **previous** challenge (the one before this run). That can be from earlier the same day or from yesterday.
- The 9:00 automatic run counts as the first challenge of the day. Any run you do later the same day will get #2, #3, etc.

## MCP configuration (Cursor)

Example `mcp.json`:

```json
{
  "mcpServers": {
    "geoguessr": {
      "command": "python",
      "args": ["/path/to/geoguessr_mcp_server.py"],
      "env": {
        "GEOGUESSR_COOKIE": "your_ncfa_cookie_value",
        "SLACK_BOT_TOKEN": "xoxb-...",
        "SLACK_CHANNEL_ID": "C0AFPA99VEE"
      }
    }
  }
}
```

## Login required for challenges

Daily challenges created by **daily_softhouse_challenge.py** use `accessLevel: 1` (private / invite-only), so only logged-in GeoGuessr users with the link can play.
