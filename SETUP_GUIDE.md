# Complete Setup Guide for GeoGuessr Daily Challenge Slack Integration

This guide will walk you through setting up automatic daily GeoGuessr challenge posts to your Slack channel.

## ✅ Step 1: Dependencies Installed

Dependencies are already installed in the virtual environment (`venv/`).

## 📝 Step 2: Configure Environment Variables

The `.env` file has been created. You need to fill in three values:

### 2.1 Get Your GeoGuessr Cookie

1. **Log into GeoGuessr** in your browser: https://www.geoguessr.com
2. **Open Developer Tools**:
   - **Mac**: Press `Cmd + Option + I`
   - **Windows/Linux**: Press `F12` or `Ctrl + Shift + I`
3. **Go to the Network tab**
4. **Refresh the page** (Cmd+R or F5)
5. **Click on any request** to `geoguessr.com` in the Network tab
6. **In the Headers section**, find **Request Headers** → **Cookie**
7. **Copy the entire value** of the `_ncfa` cookie (it's a long string)

**Example**: `_ncfa=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (very long string)

### 2.2 Set Up Slack App

Follow these steps to create a Slack app and get your bot token:

1. **Go to**: https://api.slack.com/apps
2. **Click**: "Create New App" → "From scratch"
3. **Name your app**: "GeoGuessr Daily Challenge"
4. **Select your workspace** and click "Create App"

#### Configure Bot Permissions:
1. In the left sidebar, go to **"OAuth & Permissions"**
2. Scroll to **"Scopes"** → **"Bot Token Scopes"**
3. **Add these scopes**:
   - `channels:history` - View messages in public channels
   - `channels:read` - View basic information about public channels
   - `chat:write` - Send messages as the app
   - `users:read` - View people in a workspace

#### Install App to Workspace:
1. Scroll up to **"OAuth Tokens for Your Workspace"**
2. Click **"Install to Workspace"**
3. Review permissions and click **"Allow"**
4. **Copy the Bot User OAuth Token** (starts with `xoxb-...`)

#### Get Channel ID:
1. **Open Slack** and navigate to your channel
2. **Right-click** on the channel name in the sidebar
3. Select **"View channel details"**
4. Scroll down to find the **"Channel ID"** (starts with `C`)
5. **Copy this ID**

   **Alternative method**: The channel ID is also in the URL:
   `https://yourworkspace.slack.com/archives/C1234567890`
   The part after `/archives/` is the channel ID.

#### Invite Bot to Channel:
1. In your Slack channel, type: `/invite @GeoGuessr Daily Challenge`
2. Or go to: Channel settings → Integrations → Add apps → Find your app

### 2.3 Update .env File

Open `.env` in your editor and replace the placeholder values:

```bash
GEOGUESSR_COOKIE=your_actual_ncfa_cookie_value_here
SLACK_BOT_TOKEN=xoxb-your-actual-bot-token-here
SLACK_CHANNEL_ID=C1234567890
```

**Important**: 
- Don't use quotes around the values
- Make sure there are no spaces around the `=` sign
- The cookie value is very long - copy the entire thing

## 🧪 Step 3: Test the Setup

Run the test script to verify everything works:

```bash
# Activate virtual environment
source venv/bin/activate

# Run the script
python post_daily_challenge.py
```

**Expected output**:
```
Fetching today's GeoGuessr daily challenge...
Found challenge: abc123xyz
Posting to Slack...
✅ Successfully posted daily challenge to Slack!
Challenge URL: https://www.geoguessr.com/challenge/abc123xyz
```

**If you see errors**:
- **"GEOGUESSR_COOKIE not set"**: Check your `.env` file
- **"Failed to post to Slack"**: Verify bot token and channel ID, make sure bot is invited to channel
- **"HTTP error 401"**: Your GeoGuessr cookie may have expired - get a fresh one

## ⏰ Step 4: Set Up Daily Automatic Posting

You have several options for scheduling:

### Option A: Cron Job (macOS/Linux)

1. **Open crontab editor**:
   ```bash
   crontab -e
   ```

2. **Add this line** (adjust time as needed - this posts at 9 AM daily):
   ```bash
   0 9 * * * cd /Users/almindurmis/Documents/Code/geoguessr-slack-mcp && /Users/almindurmis/Documents/Code/geoguessr-slack-mcp/venv/bin/python post_daily_challenge.py >> /tmp/geoguessr_daily.log 2>&1
   ```

   **To customize the time**: Use cron format `MINUTE HOUR * * *`
   - `0 9 * * *` = 9:00 AM daily
   - `0 12 * * *` = 12:00 PM (noon) daily
   - `30 8 * * *` = 8:30 AM daily

3. **Save and exit** (in vim: press `Esc`, type `:wq`, press Enter)

4. **Verify it's scheduled**:
   ```bash
   crontab -l
   ```

### Option B: Launchd (macOS - Recommended)

Create a plist file for macOS's launchd scheduler:

1. **Create the plist file**:
   ```bash
   nano ~/Library/LaunchAgents/com.geoguessr.dailychallenge.plist
   ```

2. **Add this content** (adjust paths and time):
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
       <key>Label</key>
       <string>com.geoguessr.dailychallenge</string>
       <key>ProgramArguments</key>
       <array>
           <string>/Users/almindurmis/Documents/Code/geoguessr-slack-mcp/venv/bin/python</string>
           <string>/Users/almindurmis/Documents/Code/geoguessr-slack-mcp/post_daily_challenge.py</string>
       </array>
       <key>WorkingDirectory</key>
       <string>/Users/almindurmis/Documents/Code/geoguessr-slack-mcp</string>
       <key>StartCalendarInterval</key>
       <dict>
           <key>Hour</key>
           <integer>9</integer>
           <key>Minute</key>
           <integer>0</integer>
       </dict>
       <key>StandardOutPath</key>
       <string>/tmp/geoguessr_daily.log</string>
       <key>StandardErrorPath</key>
       <string>/tmp/geoguessr_daily_error.log</string>
   </dict>
   </plist>
   ```

3. **Load the job**:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.geoguessr.dailychallenge.plist
   ```

4. **Start it immediately** (optional):
   ```bash
   launchctl start com.geoguessr.dailychallenge
   ```

### Option C: GitHub Actions (Cloud-based)

If you want to run this from GitHub Actions (free for public repos):

1. Create `.github/workflows/daily-challenge.yml`:
   ```yaml
   name: Post Daily Challenge
   on:
     schedule:
       - cron: '0 9 * * *'  # 9 AM UTC daily
     workflow_dispatch:  # Allows manual trigger
   
   jobs:
     post:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - uses: actions/setup-python@v4
           with:
             python-version: '3.11'
         - run: pip install -r requirements.txt
         - run: python post_daily_challenge.py
           env:
             GEOGUESSR_COOKIE: ${{ secrets.GEOGUESSR_COOKIE }}
             SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}
             SLACK_CHANNEL_ID: ${{ secrets.SLACK_CHANNEL_ID }}
   ```

2. Add secrets in GitHub repo settings → Secrets and variables → Actions

## 🎉 You're Done!

Your GeoGuessr daily challenge will now automatically post to Slack every day!

## 🔧 Troubleshooting

### Check if cron job is running:
```bash
# View cron logs
tail -f /tmp/geoguessr_daily.log

# Check launchd status
launchctl list | grep geoguessr
```

### Manual test:
```bash
source venv/bin/activate
python post_daily_challenge.py
```

### Cookie expired?
- GeoGuessr cookies can expire. If you get 401 errors, get a fresh `_ncfa` cookie and update `.env`

### Bot not posting?
- Verify bot is invited to the channel
- Check bot token is correct
- Verify channel ID is correct (starts with `C`)

## 📚 Additional Resources

- [QUICKSTART.md](QUICKSTART.md) - Quick reference
- [setup_slack_app.md](setup_slack_app.md) - Detailed Slack setup
- [README.md](README.md) - Full documentation
